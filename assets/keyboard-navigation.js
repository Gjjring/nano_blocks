document.addEventListener('keydown', function(event) {

    if (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA') {
        return;
    }

    if (event.key === 'ArrowLeft') {
        const btnPrev = document.getElementById('btn-prev');
        if (btnPrev && !btnPrev.disabled) {
            btnPrev.click();
        }
    }

    if (event.key === 'ArrowRight' || event.key === 'Enter') {
        const btnNext = document.getElementById('btn-next');
        if (btnNext && !btnNext.disabled) {
            btnNext.click();
        }
    }
});