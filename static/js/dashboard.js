(function(){
  const token = localStorage.getItem('token');
  if(!token){ window.location.href='/'; return; }
  document.getElementById('logout').addEventListener('click', (e)=>{
    e.preventDefault();
    localStorage.removeItem('token');
    window.location.href = '/';
  });
  const auth = { headers: { Authorization: `Bearer ${token}` } };
  Promise.all([
    fetch('/api/leads', auth),
    fetch('/api/properties', auth)
  ]).then(async ([leadsRes, propsRes])=>{
    if(leadsRes.status===401 || propsRes.status===401){
      localStorage.removeItem('token');
      window.location.href='/';
      return;
    }
    const leads = leadsRes.ok ? await leadsRes.json(): [];
    const props = propsRes.ok ? await propsRes.json(): [];
    document.getElementById('leadsCount').textContent = leads.length;
    document.getElementById('propsCount').textContent = props.length;
    document.getElementById('leads').innerHTML = leads.slice(0,5).map(l=>`<li>${l.name||l.email||l.phone||'Lead'}</li>`).join('');
    document.getElementById('properties').innerHTML = props.slice(0,5).map(p=>`<li>${p.title||p.location||'Property'}</li>`).join('');
  }).catch(()=>{});
})();
