import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static targets = ["generatedImage", "generateLink", "copyButton"];
  static values = { userKey: String };

  connect() {
    this.prefillGenerateLink();
    this.attachInputListeners();
  }

  prefillGenerateLink() {
    const baseUrl = window.location.origin;
    let prefillText = `${baseUrl}/g?
  style=&
  site=&
  font=&
  title=&
  subtitle=&
  eyebrow=&
  image_url=`;

    if (this.userKeyValue) {
      prefillText += `&
  key=${this.userKeyValue}`;
    }

    this.generateLinkTarget.value = prefillText;
  }

  attachInputListeners() {
    const form = this.element.querySelector('form');
    form.querySelectorAll('input, select').forEach(input => {
      input.addEventListener('input', () => this.updateGenerateLink());
    });
  }

  generate(event) {
    event.preventDefault();
    this.updateGenerateLink();
    this.generateImage();
  }

  updateGenerateLink() {
    const formData = new FormData(this.element.querySelector('form'));
    const params = new URLSearchParams();

    for (const [key, value] of formData.entries()) {
      // Skip the csrfmiddlewaretoken
      if (key !== 'csrfmiddlewaretoken') {
        params.append(key, value || '');
      }
    }

    if (this.userKeyValue) {
      params.append('key', this.userKeyValue);
    }

    const baseUrl = window.location.origin;
    const imageUrl = `/g?${params.toString()}`;
    const fullUrl = `${baseUrl}${imageUrl}`;
    const formattedUrl = fullUrl.replace(/&/g, '&\n  ').replace('?', '?\n  ');
    this.generateLinkTarget.value = formattedUrl;
  }

  generateImage() {
    const imageUrl = this.generateLinkTarget.value.replace(/\s+/g, '');
    this.generatedImageTarget.innerHTML = '<p class="text-gray-500">Generating image...</p>';

    fetch(imageUrl)
      .then(response => response.blob())
      .then(blob => {
        const objectUrl = URL.createObjectURL(blob);
        this.generatedImageTarget.innerHTML = `<img src="${objectUrl}" alt="Generated Image" class="w-full h-auto">`;
      })
      .catch(error => {
        console.error('Error generating image:', error);
        this.generatedImageTarget.innerHTML = '<p class="text-red-500">An error occurred while generating the image. Please try again.</p>';
      });
  }

  async copyGenerateLink() {
    try {
      await navigator.clipboard.writeText(this.generateLinkTarget.value);
      this.copyButtonTarget.textContent = "Copied!";
      setTimeout(() => {
        this.copyButtonTarget.textContent = "Copy";
      }, 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  }
}
