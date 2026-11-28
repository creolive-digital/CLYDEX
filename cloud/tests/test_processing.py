"""Actual bounded parsers and worker lifecycle, synthetic content only."""
from io import BytesIO
import threading
import unittest
import uuid
import wave
import zipfile
from sqlalchemy import select
from clydex.knowledge.ingestion import extract, ExtractionError
from clydex_cloud.repositories.schema import passages, jobs
import test_api_vault


def office(parts):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        for key, value in parts.items():
            z.writestr(key, value)
    return buffer.getvalue()


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        test_api_vault.ApiVaultTests.setUp(self)

    def test_ooxml_sources_and_saved_web_never_execute_instructions(self):
        docx = office({'word/document.xml': '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>CYAN document fact</w:t></w:r></w:p></w:document>'})
        pptx = office({'ppt/slides/slide2.xml': '<a:p xmlns:a="urn:fixture"><a:t>CYAN slide fact</a:t></a:p>'})
        xlsx = office({'xl/workbook.xml': '<x:workbook xmlns:x="urn:fixture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><x:sheet name="Fixture" r:id="r1"/></x:workbook>',
            'xl/_rels/workbook.xml.rels': '<Relationships><Relationship Id="r1" Target="worksheets/sheet1.xml"/></Relationships>',
            'xl/worksheets/sheet1.xml': '<x:worksheet xmlns:x="urn:fixture"><x:c r="A2"><x:f>NEVER_EXECUTE()</x:f><x:v>CYAN cached fact</x:v></x:c></x:worksheet>'})
        for name, content, location in (('fixture.docx', docx, 'paragraph 1'), ('fixture.pptx', pptx, 'slide 2'), ('fixture.xlsx', xlsx, 'cell A2')):
            result = extract(name, content)
            self.assertEqual(result.status, 'ready')
            self.assertIn('CYAN', result.passages[0].text)
            self.assertIn(location, result.passages[0].location)
            self.assertNotIn('NEVER_EXECUTE', result.passages[0].text)
        web = extract('saved.html', b'<p>CYAN fact</p><script>NEVER_EXECUTE()</script><img src="https://never-fetch.invalid/private">')
        self.assertNotIn('NEVER_EXECUTE', web.passages[0].text)

    def test_scanned_pdf_and_pcm_audio_report_actual_processing_limitations(self):
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        document = BytesIO()
        writer.write(document)
        pdf = extract('scan.pdf', document.getvalue())
        self.assertEqual(pdf.status, 'needs_ocr')
        stream = BytesIO()
        with wave.open(stream, 'wb') as sound:
            sound.setnchannels(1)
            sound.setsampwidth(2)
            sound.setframerate(16000)
            sound.writeframes(b'\0\0' * 160)
        self.assertEqual(extract('fixture.wav', stream.getvalue()).status, 'needs_transcription')

    def test_archive_decompression_and_xml_entities_are_rejected(self):
        bomb = office({'word/document.xml': 'A' * 1_000_000})
        with self.assertRaises(ExtractionError):
            extract('bomb.docx', bomb)
        unsafe = office({'word/document.xml': '<!DOCTYPE x [<!ENTITY a SYSTEM "file:///private">]><x>&a;</x>'})
        with self.assertRaises(ExtractionError):
            extract('unsafe.docx', unsafe)

    def test_cancelled_worker_cannot_publish_chunks_after_document_deletion(self):
        collection = self.runtime.vault.create_collection(self.actor, {'title': 'Cancellation fixture', 'description': ''})
        uploaded = self.runtime.vault.upload(self.actor, collection['id'], 'fixture.txt', b'Synthetic cancellation evidence', str(uuid.uuid4()))
        entered, release = threading.Event(), threading.Event()
        def parser(name, content, cancel):
            entered.set()
            release.wait(5)
            return extract(name, content).public()
        self.runtime.worker.parser = parser
        thread = threading.Thread(target=self.runtime.worker.tick)
        thread.start()
        try:
            self.assertTrue(entered.wait(3))
            self.runtime.vault.delete_document(self.actor, uploaded['document_id'], uploaded['revision'])
        finally:
            release.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        with self.db.transaction() as c:
            self.assertEqual(c.execute(select(passages)).all(), [])
            self.assertEqual(c.execute(select(jobs.c.status)).scalar(), 'cancelled')
