const TNUExport = (() => {
  async function download(format, results, parameters) {
    const response=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({format,data:results,parameters})});
    if(!response.ok) throw new Error((await response.json()).error||'Não foi possível exportar.');
    const blob=await response.blob(), link=document.createElement('a'); link.href=URL.createObjectURL(blob);
    link.download=`tnu-resultados.${format==='markdown'?'md':format}`; link.click(); URL.revokeObjectURL(link.href);
  }
  function pdf(results, parameters){const {jsPDF}=window.jspdf, doc=new jsPDF();doc.setFontSize(20);doc.text('TNU — Resultados da busca',14,20);doc.setFontSize(10);doc.text(`Consulta: ${parameters.query} (${parameters.lang_from} → ${parameters.lang_to})`,14,29);let y=40;results.forEach((r,i)=>{doc.text(`${i+1}. ${r.lemma} [${r.lang}]  score ${r.score}  D ${r.distance?.D ?? '-' }  ${r.relation??''}`,14,y);y+=8;if(y>280){doc.addPage();y=20}});doc.save('tnu-resultados.pdf')}
  return {download,pdf};
})();
