import type {Values} from '../../types/bridge';
export type CloudOperation = 'login'|'refresh'|'logout'|'reload'|'collection.create'|'collection.delete'|'document.delete'|'document.reprocess'|'document.versions'|'document.upload'|'document.version'|'note.create'|'search'|'ask'|'device.pair'|'device.approve'|'device.revoke'|'device.rotate'|'sync.configure'|'sync.enqueue'|'sync.push'|'sync.pull'|'sync.apply'|'sync.theme'|'sync.discard'|'cache.add'|'cache.remove'|'cache.clear'|'offline.search'|'offline.ask';
export interface Collection {id:string;title:string;description:string;revision:number}
export interface Document {id:string;collection_id:string;name:string;title:string;version:number;revision:number;status:string;size_bytes:number;sha256:string}
export interface Device {id:string;display_name:string;platform:string;scopes:string[];last_seen:number;revoked_at:number|null;credential_version:number}
export interface Citation {citation_id:string;document_id:string;version:number;revision:number;name:string;location:string;excerpt:string;score?:number}
export interface SearchResult {items:Citation[];insufficient_evidence:boolean;mode:string}
export interface GroundedAnswer {answer:string;citations:string[];sources?:Citation[];insufficient_evidence:boolean}
export type Category = 'knowledge'|'memory'|'history'|'preferences'|'workflows'|'devices'|'themes';
export const categories:Category[]=['knowledge','memory','history','preferences','workflows','devices','themes'];
export interface CloudSnapshot {
  configuration:{endpoint:string;enabled:boolean};status:string;account_id:string;error:string;revision:number;
  selections:{id:string;name:string;size_bytes:number;sha256:string}[];
  results:Partial<Record<CloudOperation,unknown>> & {
    reload?:{collections:{items:Collection[]};documents:{items:Document[];truncated:boolean};devices:{items:Device[]};
      jobs:{items:{id:string;document_id:string;status:string;error_code:string;attempts:number}[]};
      usage:{document_bytes:number;quota_bytes:number;pending_delete_bytes:number};
      capabilities:{database:string;embedding_configured:boolean;server_managed_encryption:boolean;e2ee:boolean}};
    search?:SearchResult;'offline.search'?:SearchResult;ask?:GroundedAnswer;'offline.ask'?:GroundedAnswer;
    'device.pair'?:{id:string;pairing_token:string;expires_in:number;approved:boolean};
    'document.versions'?:{items:{version:number;sha256:string;size_bytes:number;parser:string}[]};
  };
  synchronization?:{policy:Record<Category,boolean>;cursor:number;outbox:{id:string;category:Category;entity_id:string;status:string;attempts:number;error:string}[];
    inbox:{sequence:number;category:Category;entity_id:string;version:number;deleted:boolean;payload:Values}[]};
  cache?:{items:{document_id:string;revision:number;expires:number;size_bytes:number}[];size_bytes:number;revocation:string};
}
