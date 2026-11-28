import type {Json,Values} from '../../types/bridge';

export type NodeKind='input'|'note'|'tool'|'condition'|'delay'|'approval'|'loop'|'output';
export interface WorkflowNode {id:string;kind:NodeKind;config:Values;x:number;y:number}
export interface WorkflowEdge {from:string;to:string;port:'next'|'true'|'false'}
export interface Workflow {contract_version:2;id:string;name:string;inputs:Values;nodes:WorkflowNode[];edges:WorkflowEdge[];timeout:number}
export interface OperatingRecord {id:string;revision:number;value:Values}
export interface InstalledTool {id:string;description:string;scope:string;risk:string;timeout:number;available:boolean;read_only:boolean;arguments:Values;results:Values;destinations:string[];idempotent:boolean}
export interface Run {id:string;workflow_id:string;revision:number;status:string;started_at:number;finished_at:number|null;nodes:Record<string,string>}
export interface OperatingSnapshot {
 revision:number; records:Record<string,OperatingRecord[]>; selections:{id:string;kind:string;name:string;path:string;sha256:string;expires_in:number}[];
 activity?:{id:number;created_at:string;digest:string;tool:string;outcome:string}[];tools:InstalledTool[];runs:Run[];result:{operation?:string;data?:Json};error:string;routines:string[];feed_kinds:string[];
 services:Record<string,{operations:string[];scopes:string[]}>;feeds:Record<string,Values>;monitoring:Values;
 armed:string[];polling:boolean;capture_armed:boolean;plugin_health:Record<string,string>;plugin_trust:string;acceptance:string;
 workflow_replicas:{id:string;version:number;payload:Values}[];
}
export type OperatingOperation='workflow.restore'|'workflow.versions'|'workflow.save'|'workflow.enable'|'workflow.preview'|'workflow.run'|'workflow.import'|'routine.create'|'trigger.save'|'trigger.arm'|'feed.save'|'feed.refresh'|'feed.polling'|'integration.save'|'profile.save'|'record.delete'|'credential.set'|'tool.invoke'|'developer.analyze'|'mcp.save'|'mcp.discover'|'mcp.review'|'plugin.inspect'|'plugin.install'|'plugin.enable'|'capture.arm'|'monitor.refresh'|'result.clear';
