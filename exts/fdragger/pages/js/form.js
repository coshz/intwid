document.addEventListener('DOMContentLoaded', function() {
    const saveOptions = (event) => {
        event.preventDefault();
        const saveto_value = document.getElementById("saveto").value;
        const name_value = document.getElementById("name").value;
        chrome.storage.sync.set(
            { saveto: saveto_value, name: name_value },
            () => {
                document.getElementById("saveto").value=saveto_value;
                document.getElementById("name").value=name_value;
                const status_ = document.getElementById("status");
                status_.innerHTML = "setting saved.";
                setTimeout(function() {
                    status_.innerHTML = "";
                },3000);
            }
        );
    };
    document.getElementById('options-form').addEventListener('submit', saveOptions);
});