// landing.js — "See how it works" video modal

(function () {
    const modal = document.getElementById("video-modal");
    const openBtn = document.querySelector("[data-video-open]");
    if (!modal || !openBtn) return;

    const content = modal.querySelector(".video-modal-content");
    const closeBtn = modal.querySelector("[data-video-close]");
    const iframe = modal.querySelector("iframe");

    function openModal() {
        // Load the video fresh each time so it always starts stopped
        iframe.src = iframe.dataset.src;
        modal.hidden = false;
        document.body.classList.add("modal-open");
        closeBtn.focus();
    }

    function closeModal() {
        if (modal.hidden) return;
        modal.hidden = true;
        // Unloading the iframe stops playback and audio completely
        iframe.src = "about:blank";
        document.body.classList.remove("modal-open");
        openBtn.focus();
    }

    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);

    // Click on the backdrop (outside the content box) closes the modal
    modal.addEventListener("click", function (event) {
        if (!content.contains(event.target)) closeModal();
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") closeModal();
    });
})();
