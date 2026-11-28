"""Bounded format extraction. Content is data: never execute macros, code or SQL.

Run untrusted parsers in the cloud's owned timeout/resource-limited child process.
These checks are not an operating-system sandbox or antivirus certification.
"""
from html.parser import HTMLParser
from io import BytesIO
import posixpath
import re
import struct
import unicodedata
import wave
import zipfile

from clydex.knowledge.models import Extraction, chunks

MAX_FILE = 10 * 1024 * 1024
MAX_TEXT = 1_000_000
MAX_CHUNKS = 2000
TEXT_SUFFIXES = frozenset(('.txt', '.md', '.markdown', '.py', '.js', '.ts', '.tsx', '.jsx', '.java',
    '.cs', '.cpp', '.c', '.h', '.rs', '.go', '.sql', '.json', '.yaml', '.yml', '.toml', '.csv', '.log'))
FORMATS = {'text': 'UTF-8 text/Markdown/code/SQL; literal, never executed',
    'pdf': 'pypdf text layer, bounded pages; scanned/encrypted PDFs require another approved path',
    'docx': 'Word OOXML paragraphs/tables; section/paragraph locations, not invented page numbers',
    'xlsx': 'Excel OOXML cached values; sheet/cell locations, formulas never evaluated',
    'pptx': 'PowerPoint OOXML text; slide locations',
    'html': 'Saved HTML visible text only; scripts/styles/remote resources never executed/fetched',
    'png/jpeg': 'Verified container metadata/storage only; OCR unavailable until explicitly configured',
    'wav': 'PCM container metadata/storage only; transcription unavailable until explicitly configured',
    'legacy Office/archives/other audio': 'Unsupported; convert explicitly with a trusted offline tool'}


class ExtractionError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def filename(value: str) -> str:
    if (not isinstance(value, str) or not 1 <= len(value) <= 180 or value in ('.', '..')
            or any(c in value for c in '/\\:\x00') or any(unicodedata.category(c)[0] == 'C' for c in value)):
        raise ExtractionError('invalid_filename')
    return value


def suffix(name: str) -> str:
    return '.' + name.rsplit('.', 1)[-1].lower() if '.' in name else ''


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.blocked = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'template'):
            self.blocked += 1
        elif tag in ('p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'tr') and not self.blocked:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'template'):
            self.blocked = max(0, self.blocked - 1)

    def handle_data(self, data):
        if not self.blocked:
            self.parts.append(data)


def safe_zip(data: bytes) -> zipfile.ZipFile:
    try:
        archive = zipfile.ZipFile(BytesIO(data))
        entries = archive.infolist()
        if len(entries) > 1024 or sum(x.file_size for x in entries) > 32 * 1024 * 1024:
            raise ExtractionError('archive_expansion_limit')
        for item in entries:
            name = item.filename
            if (name.startswith(('/', '\\')) or '\\' in name or ':' in name
                    or '..' in name.split('/') or item.flag_bits & 1
                    or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ExtractionError('unsafe_archive_member')
            if item.file_size > 8 * 1024 * 1024 or item.file_size / max(1, item.compress_size) > 200:
                raise ExtractionError('archive_expansion_limit')
        if '[Content_Types].xml' not in archive.namelist():
            raise ExtractionError('not_office_ooxml')
        if any('vbaproject' in n.lower() or n.lower().endswith(('.exe', '.dll')) for n in archive.namelist()):
            raise ExtractionError('active_office_content')
        return archive
    except (zipfile.BadZipFile, RuntimeError):
        raise ExtractionError('invalid_office_container') from None


def xml(archive: zipfile.ZipFile, name: str):
    from defusedxml.ElementTree import fromstring
    data = archive.read(name)
    if b'\x00' in data or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ExtractionError('unsafe_xml')
    root = fromstring(data, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    if sum(1 for _ in root.iter()) > 100000:
        raise ExtractionError('xml_node_limit')
    return root


def ooxml(data: bytes, kind: str) -> Extraction:
    class BoundedPassages(list):
        size = 0

        def extend(self, values):
            for value in values:
                self.size += len(value.text)
                if len(self) >= MAX_CHUNKS or self.size > MAX_TEXT:
                    raise ExtractionError('extracted_content_limit')
                self.append(value)
    result = BoundedPassages()
    with safe_zip(data) as archive:
        names = archive.namelist()
        if kind == '.docx':
            if 'word/document.xml' not in names:
                raise ExtractionError('office_type_mismatch')
            root = xml(archive, 'word/document.xml')
            for index, node in enumerate(root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')):
                text = ' '.join(n.text or '' for n in node.iter() if n.tag.endswith('}t'))
                result.extend(chunks(text, f'paragraph {index + 1}', len(result)))
        elif kind == '.pptx':
            slides = sorted((n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)),
                            key=lambda n: int(re.search(r'slide(\d+)\.xml', n)[1]))
            if not slides or len(slides) > 500:
                raise ExtractionError('slide_limit_or_type_mismatch')
            for name in slides:
                text = ' '.join(n.text or '' for n in xml(archive, name).iter() if n.tag.endswith('}t'))
                number = re.search(r'slide(\d+)\.xml', name)[1]
                result.extend(chunks(text, f'slide {number}', len(result)))
        else:
            if 'xl/workbook.xml' not in names:
                raise ExtractionError('office_type_mismatch')
            shared = []
            if 'xl/sharedStrings.xml' in names:
                shared = [''.join(x.itertext()) for x in xml(archive, 'xl/sharedStrings.xml')]
            relationships = {}
            for rel in xml(archive, 'xl/_rels/workbook.xml.rels'):
                if rel.attrib.get('TargetMode') != 'External':
                    target = rel.attrib.get('Target', '')
                    path = posixpath.normpath('xl/' + target) if not target.startswith('/') else target[1:]
                    if not path.startswith('xl/worksheets/') or '..' in target.split('/'):
                        continue
                    relationships[rel.attrib.get('Id')] = path
            for sheet in xml(archive, 'xl/workbook.xml').iter():
                if not sheet.tag.endswith('}sheet'):
                    continue
                ref = sheet.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                path = relationships.get(ref)
                if path not in names:
                    continue
                for cell in xml(archive, path).iter():
                    if not cell.tag.endswith('}c'):
                        continue
                    values = [n.text or '' for n in cell.iter() if n.tag.endswith(('}v', '}t'))]
                    if cell.attrib.get('t') == 's' and values:
                        try:
                            index = int(values[0])
                            if index < 0:
                                raise ValueError()
                            values = [shared[index]]
                        except (ValueError, IndexError):
                            raise ExtractionError('invalid_shared_string') from None
                    result.extend(chunks(' '.join(values),
                        f"sheet {sheet.attrib.get('name', '?')[:70]}; cell {cell.attrib.get('r', '?')[:20]}", len(result)))
        if len(result) > MAX_CHUNKS or sum(len(p.text) for p in result) > MAX_TEXT:
            raise ExtractionError('extracted_content_limit')
    return Extraction('ready' if result else 'empty', 'ooxml-defusedxml-v1', tuple(result))


def extract(name: str, data: bytes) -> Extraction:
    filename(name)
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_FILE:
        raise ExtractionError('file_size_limit')
    kind = suffix(name)
    if kind in TEXT_SUFFIXES or kind in ('.html', '.htm'):
        if len(data) > MAX_TEXT or b'\x00' in data:
            raise ExtractionError('text_size_or_binary')
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError:
            raise ExtractionError('utf8_required') from None
        if kind in ('.html', '.htm'):
            parser = VisibleHTML()
            parser.feed(text)
            text = ''.join(parser.parts)
        result = chunks(text, 'text')
        return Extraction('ready' if result else 'empty', 'literal-text-v1', tuple(result))
    if kind == '.pdf':
        if not data.startswith(b'%PDF-'):
            raise ExtractionError('pdf_signature_mismatch')
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ExtractionError('encrypted_pdf_not_supported')
        if len(reader.pages) > 300:
            raise ExtractionError('pdf_page_limit')
        result = []
        for index, page in enumerate(reader.pages):
            contents = page.get_contents()
            if contents is not None and len(contents.get_data()) > 8 * 1024 * 1024:
                raise ExtractionError('pdf_content_stream_limit')
            result.extend(chunks(page.extract_text() or '', f'page {index + 1}', len(result)))
            if len(result) > MAX_CHUNKS or sum(len(p.text) for p in result) > MAX_TEXT:
                raise ExtractionError('extracted_content_limit')
        return Extraction('ready' if result else 'needs_ocr', 'pypdf-text-layer-v1', tuple(result),
                          '' if result else 'ocr_not_configured')
    if kind in ('.docx', '.xlsx', '.pptx'):
        return ooxml(data, kind)
    if kind in ('.png', '.jpg', '.jpeg'):
        if kind == '.png':
            if len(data) < 33 or not data.startswith(b'\x89PNG\r\n\x1a\n') or data[12:16] != b'IHDR':
                raise ExtractionError('image_signature_mismatch')
            width, height = struct.unpack('>II', data[16:24])
            if not 0 < width * height <= 20_000_000:
                raise ExtractionError('image_pixel_limit')
        elif not (data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9')):
            raise ExtractionError('image_signature_mismatch')
        return Extraction('needs_ocr', 'image-container-v1', warning='ocr_not_configured')
    if kind == '.wav':
        try:
            with wave.open(BytesIO(data)) as audio:
                if (audio.getnchannels() not in (1, 2) or audio.getsampwidth() != 2
                        or not 8000 <= audio.getframerate() <= 48000 or audio.getnframes() > 48000 * 300
                        or audio.getnframes() * audio.getnchannels() * 2 > len(data)):
                    raise ExtractionError('audio_bounds')
        except (wave.Error, EOFError):
            raise ExtractionError('audio_container_invalid') from None
        return Extraction('needs_transcription', 'wav-metadata-v1', warning='transcription_not_configured')
    raise ExtractionError('unsupported_format')
