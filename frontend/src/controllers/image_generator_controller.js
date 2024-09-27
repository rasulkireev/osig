import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static targets = ["form"];

  generate(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const searchParams = new URLSearchParams(formData);

    const generatedImageDiv = document.getElementById('generated-image');
    generatedImageDiv.innerHTML = '<p class="text-gray-500">Generating image...</p>';

    fetch(`/g?${searchParams.toString()}`)
      .then(response => response.blob())
      .then(blob => {
        const imageUrl = URL.createObjectURL(blob);
        generatedImageDiv.innerHTML = `<img src="${imageUrl}" alt="Generated Image" class="w-full h-auto">`;
      })
      .catch(error => {
        console.error('Error generating image:', error);
        generatedImageDiv.innerHTML = '<p class="text-red-500">An error occurred while generating the image. Please try again.</p>';
      });
  }
}
