document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysis-form');
    const fileInput = form.querySelector('input[type="file"]');
    const submitButton = form.querySelector('button[type="submit"]');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Validate file types
    function validateFileType(file) {
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        return allowedTypes.includes(file.type);
    }

    // Validate the form inputs
    function validateForm() {
        const inputs = form.querySelectorAll('input[type="text"], textarea');
        for (let input of inputs) {
            if (input.value.trim() === '') {
                return false;
            }
        }
        return true;
    }

    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && !validateFileType(file)) {
            alert('Please upload a PDF or DOCX file only.');
            fileInput.value = '';
        }
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            alert('Please fill in all fields.');
            return;
        }

        console.log('Form submission initiated.');

        // Log form input values
        const textInputs = form.querySelectorAll('input[type="text"], textarea');
        textInputs.forEach(input => {
            console.log(`Input Name: ${input.name}, Value: ${input.value}`);
        });

        // Log file information if a file is selected
        const file = fileInput.files[0];
        if (file) {
            console.log(`Selected file: ${file.name}, Type: ${file.type}, Size: ${file.size} bytes`);
        } else {
            console.log('No file selected.');
        }

        loadingSpinner.style.display = 'block';
        submitButton.disabled = true;

        try {
            const formData = new FormData(form);

            // Log FormData entries
            for (let [key, value] of formData.entries()) {
                if (value instanceof File) {
                    console.log(`FormData Entry - ${key}: File - Name: ${value.name}, Type: ${value.type}, Size: ${value.size}`);
                } else {
                    console.log(`FormData Entry - ${key}: ${value}`);
                }
            }

            const response = await fetch('https://market-research-ai-production.up.railway.app/analyze', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                    // 'Content-Type' is intentionally omitted to let the browser set it, including the boundary
                }
            });

            console.log(`Received response with status: ${response.status}`);

            const responseText = await response.text();
            console.log(`Response Text: ${responseText}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}. Response: ${responseText}`);
            }

            let data;
            try {
                data = JSON.parse(responseText);
                console.log('Parsed JSON Response:', data);
            } catch (jsonError) {
                console.error('Error parsing JSON:', jsonError);
                throw new Error('Invalid JSON response from server.');
            }

            displayAnalysisResults(data);
        } catch (error) {
            console.error('Error during form submission:', error);
            alert('An error occurred during the analysis. Please check the console for more details.');
        } finally {
            loadingSpinner.style.display = 'none';
            submitButton.disabled = false;
        }
    });

    function displayAnalysisResults(analysisData) {
        // Show the report section
        const reportSection = document.getElementById('report-section');
        reportSection.style.display = 'block';

        // Populate the TAM, SAM, SOM data
        const tamElement = document.getElementById('tam');
        const samElement = document.getElementById('sam');
        const somElement = document.getElementById('som');

        if (tamElement && samElement && somElement) {
            tamElement.innerText = analysisData.tam || 'N/A';
            samElement.innerText = analysisData.sam || 'N/A';
            somElement.innerText = analysisData.som || 'N/A';
        } else {
            console.error('One or more analysis result elements are missing in the DOM.');
            alert('An error occurred while displaying the analysis results.');
            return;
        }

        // Ensure download button has only one event listener
        const downloadButton = document.getElementById('download-btn');
        const newDownloadButton = downloadButton.cloneNode(true);
        downloadButton.parentNode.replaceChild(newDownloadButton, downloadButton);

        newDownloadButton.addEventListener('click', () => {
            loadingSpinner.style.display = 'block';
            newDownloadButton.disabled = true;

            const reportSection = document.getElementById('report-section');

            // Check if html2pdf is available
            if (typeof html2pdf === 'undefined') {
                alert('The PDF generation library is not loaded. Please ensure that html2pdf.js is properly included.');
                loadingSpinner.style.display = 'none';
                newDownloadButton.disabled = false;
                return;
            }

            // Generate PDF from the report section
            html2pdf(reportSection, {
                margin:       0.5,
                filename:     'Market_Analysis_Report.pdf',
                image:        { type: 'jpeg', quality: 0.98 },
                html2canvas:  { scale: 2 },
                jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
            })
            .then(() => {
                loadingSpinner.style.display = 'none';
                newDownloadButton.disabled = false;
                console.log('PDF generation completed successfully.');
            })
            .catch(error => {
                console.error('Error generating PDF:', error);
                alert('An error occurred while generating the PDF: ' + error.message);
                loadingSpinner.style.display = 'none';
                newDownloadButton.disabled = false;
            });
        });
    }
});
