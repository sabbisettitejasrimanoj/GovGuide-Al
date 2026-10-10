const chat=document.getElementById("chat"),form=document.getElementById("form");
const input=document.getElementById("question"),send=document.getElementById("send");
let sessionId=null;
function bubble(text,role,sources=[]){
 const div=document.createElement("div");div.className="bubble "+role;
 const body=document.createElement("div");body.textContent=text;div.appendChild(body);
 if(sources.length){
  const foot=document.createElement("div");foot.className="sources";
  foot.appendChild(document.createTextNode("Sources: "));
  sources.forEach((s,i)=>{
   if(i)foot.appendChild(document.createTextNode(" • "));
   const label=s.file+" ("+s.status+")";
   if(s.url && /^https:\/\//.test(s.url)){
    const a=document.createElement("a");a.href=s.url;a.target="_blank";a.rel="noopener noreferrer";a.textContent=label;foot.appendChild(a);
   }else{foot.appendChild(document.createTextNode(label));}
  });div.appendChild(foot);
 }
 chat.appendChild(div);chat.scrollTop=chat.scrollHeight;return div;
}
async function ask(question){
 if(!question.trim())return;
 bubble(question,"user");input.value="";send.disabled=true;
 const pending=bubble("Searching the knowledge base...","assistant");
 try{
  const r=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message:question,session_id:sessionId})});
  const data=await r.json();pending.remove();
  if(!r.ok)throw new Error(data.error||"Request failed");
  sessionId=data.session_id;bubble(data.answer,"assistant",data.sources);
 }catch(e){pending.remove();bubble("Error: "+e.message,"assistant");}
 finally{send.disabled=false;input.focus();}
}
form.addEventListener("submit",e=>{e.preventDefault();ask(input.value)});
document.querySelectorAll("[data-q]").forEach(b=>b.addEventListener("click",()=>ask(b.dataset.q)));
