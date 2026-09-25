const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export type Endpoint = {id:string;name:string;token:string;created_at:string};
export type Captured = {id:string;method:string;path:string;body_preview:string|null;body_size:number;source_ip:string;content_type:string|null;received_at:string};
export async function api<T>(path:string, options:RequestInit = {}): Promise<T> { const auth = localStorage.getItem("rbx_token"); const r=await fetch(`${API}${path}`,{...options,headers:{"Content-Type":"application/json",...(auth?{Authorization:`Bearer ${auth}`}:{}) ,...options.headers}}); if(!r.ok) throw new Error((await r.json().catch(()=>null))?.detail ?? `Request failed (${r.status})`); return r.json(); }
export { API };
