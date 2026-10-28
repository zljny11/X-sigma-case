'use strict';
const $ = id => document.getElementById(id);
let dogs = [], services = [], groomers = [], dogRequest = 0, scheduleRequest = 0;
const localDate = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
async function api(path, options) {
  const response = await fetch(`/api${path}`, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || '请求失败，请稍后再试。');
  return data;
}
function option(select, items, key, text, placeholder) {
  select.replaceChildren();
  if(placeholder) select.add(new Option(placeholder, ''));
  items.forEach(item => select.add(new Option(item[text],item[key])));
}
function updateSummary() {
  const dog = dogs.find(d=>d.dog_id === Number($('dog').value));
  const service = services.find(s=>s.service_id === Number(document.querySelector('input[name="service"]:checked')?.value));
  $('summary-dog').textContent = dog?.dog_name || '等待一位小可爱';
  $('summary-breed').textContent = dog?.breed || '今天也要闪闪发光';
  $('dog-detail').textContent = dog ? `${dog.dog_name} · ${dog.breed}` : '请选择这位家长的狗狗。';
  $('summary-service').textContent = service ? `${service.service_name === 'Wash' ? '洗护' : '美容'} · ${service.service_name}` : '尚未选择';
  $('summary-groomer').textContent = groomers.find(g=>g.groomer_id === Number($('groomer').value))?.groomer_name || '尚未选择';
  const date=$('date').value,time=$('time').value;
  if(date && time){
    const end=new Date(`${date}T${time}`);end.setHours(end.getHours()+1);
    const endTime=`${String(end.getHours()).padStart(2,'0')}:${String(end.getMinutes()).padStart(2,'0')}`;
    $('summary-time').textContent=`${date} ${time}–${endTime}${end.getDate()!==new Date(`${date}T${time}`).getDate()?'（次日）':''}`;
  } else $('summary-time').textContent='尚未选择';
}
function message(text, error=false) {
  $('message').hidden=false; $('message').className=error?'error':''; $('message').textContent=text;
  $('message').focus();
}
async function loadDogs() {
  const token=++dogRequest; dogs=[];
  option($('dog'),[], 'dog_id','dog_name','加载中…'); $('dog').disabled=true; updateSummary();
  try {
    const items=await api(`/parents/${$('parent').value}/dogs`);
    if(token!==dogRequest)return;
    dogs=items; option($('dog'),dogs,'dog_id','dog_name',dogs.length?'请选择狗狗':'暂无狗狗');
    $('dog').disabled=!dogs.length; updateSummary();
  } catch(error){ if(token===dogRequest){option($('dog'),[],'dog_id','dog_name','加载失败，请重新选择家长');message(error.message,true);} }
}
async function showSchedule() {
  const token=++scheduleRequest, id=$('schedule-groomer').value;
  $('schedule-message').className=''; $('schedule-message').textContent='正在加载日程…';
  $('schedule-list').replaceChildren();$('booking-count').textContent='…';
  try {
    const bookings = await api(`/groomers/${id}/bookings`);
    if(token!==scheduleRequest)return;
    $('schedule-message').textContent=''; $('booking-count').textContent=`${bookings.length} 个预约`;
    if(!bookings.length){const empty=document.createElement('div');empty.className='empty';empty.innerHTML='<b>☀</b>日程还是空白，期待下一位小可爱。';$('schedule-list').append(empty);}
    bookings.forEach(b=>{
      const card=document.createElement('article');card.className='appointment';
      const date=document.createElement('time');date.dateTime=b.start_time;
      date.textContent=`${b.start_time.slice(11)}–${b.end_time.slice(11)}`;
      const day=document.createElement('small');day.textContent=b.start_time.slice(0,10)+(b.end_time.slice(0,10)!==b.start_time.slice(0,10)?' · 跨日':'');date.append(day);
      const details=document.createElement('div');const title=document.createElement('h4');title.textContent=b.dog_name;
      const parent=document.createElement('p');parent.textContent=`家长 ${b.parent_name} · ${b.breed}`;
      const service=document.createElement('span');service.className='service-pill';service.textContent=`${b.service_name} · 60 min`;
      details.append(title,parent,service);card.append(date,details);$('schedule-list').append(card);
    });
  }catch(error){if(token===scheduleRequest){$('schedule-message').className='error';$('schedule-message').textContent=error.message;$('booking-count').textContent='加载失败';}}
}
function switchView(schedule) {
  $('parent-view').hidden=schedule;$('groomer-view').hidden=!schedule;
  $('parent-tab').classList.toggle('active',!schedule);$('groomer-tab').classList.toggle('active',schedule);
  $('parent-tab').setAttribute('aria-selected',String(!schedule));$('groomer-tab').setAttribute('aria-selected',String(schedule));
  if(schedule)showSchedule();
}
$('parent-tab').onclick=()=>switchView(false);$('groomer-tab').onclick=()=>switchView(true);
$('schedule-groomer').onchange=showSchedule;$('refresh').onclick=showSchedule;
$('parent').onchange=loadDogs;
['dog','groomer','date','time'].forEach(id=>$(id).addEventListener('change',updateSummary));
$('booking-form').onsubmit=async event=>{
  event.preventDefault(); $('submit').disabled=true;
  const groomerId=Number($('groomer').value);
  try {
    const result=await api('/bookings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({parent_id:Number($('parent').value),dog_id:Number($('dog').value),groomer_id:groomerId,service_id:Number(document.querySelector('input[name="service"]:checked')?.value),start_time:`${$('date').value}T${$('time').value}`})});
    message(`预约成功！编号 #${result.booking_id}，${result.start_time.replace('T',' ')} 至 ${result.end_time.replace('T',' ')}。`);
    const link=document.createElement('a');link.href='#schedule';link.textContent='查看美容师日程 →';link.onclick=e=>{e.preventDefault();$('schedule-groomer').value=String(groomerId);switchView(true);};$('message').append(link);
  }catch(error){message(error.message,true);}finally{$('submit').disabled=false;}
};
async function init(){
  $('submit').disabled=true;$('date').value=localDate();
  try{
    const [parents,gs,ss]=await Promise.all([api('/parents'),api('/groomers'),api('/services')]);
    groomers=gs;services=ss;
    option($('parent'),parents,'parent_id','parent_name');option($('groomer'),groomers,'groomer_id','groomer_name','请选择美容师');option($('schedule-groomer'),groomers,'groomer_id','groomer_name');
    services.forEach((s,index)=>{
      const label=document.createElement('label');label.className='service-card';
      const input=document.createElement('input');input.type='radio';input.name='service';input.value=s.service_id;input.required=true;input.checked=index===0;input.onchange=updateSummary;
      const icon=document.createElement('span');icon.className='service-icon';icon.textContent=s.service_name==='Wash'?'♧':'✂';icon.setAttribute('aria-hidden','true');
      const copy=document.createElement('span'),title=document.createElement('strong'),sub=document.createElement('small');
      title.textContent=s.service_name==='Wash'?'泡泡洗护 Wash':'精致美容 Grooming';sub.textContent='60 分钟 · 温柔护理';copy.append(title,sub);label.append(input,icon,copy);$('service-options').append(label);
    });
    await loadDogs();updateSummary();$('submit').disabled=false;
  }catch(error){message(`初始化失败：${error.message} 请刷新页面重试。`,true);}
}
init();
