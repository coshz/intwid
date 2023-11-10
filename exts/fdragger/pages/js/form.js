document.addEventListener('DOMContentLoaded', function() {
    const saveOptions = (event) => {
        event.preventDefault();
        const saveto_value = document.getElementById("saveto").value;
        chrome.storage.sync.set(
            { saveto: saveto_value },
            () => {
                const option_saveto = document.getElementById("saveto");
                option_saveto.placeholder=saveto_value;
                option_saveto.value=saveto_value;
            }
        );
    };
    document.getElementById('options-form').addEventListener('submit', saveOptions);
});