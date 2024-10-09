# OG Image Generator Documentation

## Overview

The OG Image Generator allows you to create custom Open Graph images for your website. You can specify various parameters to customize the image according to your needs.

## URL

The url for all images will be the same:

`https://osig.app/g/`

## Parameters

Parameters will vary depending on the style. All of them are optional, but if you don't pass anything it will look like sh\*t.

![OG Image Generator Parameters](https://osig.app/static/vendors/images/no-params-example.0b515a8143fb.png)

Below is a list of all parameters we currently support:

*   **key**: Your API key. Can be found in your [settings](/settings) page, if you are registered.
*   **style**: Image style (default: "base")
    *   \- [base](#base)
    *   \- [logo](#logo)
*   **site**: This dictates the size of the image (default: "x")
    *   \- x (1600 by 900)
    *   \- meta (1200 by 630)
*   **font**: Font to use for text (more will be added)
    *   \- [helvetica](#Helvetica)
    *   \- [markerfelt](#Markerfelt)
    *   \- [papyrus](#Papyrus)
*   **title**: Main title text
*   **subtitle**: Subtitle text
*   **eyebrow**: Eyebrow text
*   **image\_url**: URL of the background image

## Usage

The url for all images will be the same:

```
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content="{ generated_image_url }"/>
```

## Examples

### Base Style

This is useful for general pages like Articles, Tutorial, News pages. Pro tip, you can generate the background image using AI. Those work super well.

Here is what gets generated for my site's articles:

![Base OG Image Example](https://osig.app/static/vendors/images/base-example.73fce7ac82c5.png)

This is the that I use to generate the image:

```
https://osig.app/g?
  site=x
  &style=base
  &font=helvetica
  &title=10 Years of Great Books
  &subtitle=I'm starting a 10 Year Reading Plan proposed in the 1st Volume (The Great Conversation) of the "Great Books of the Western World" series.
  &eyebrow=Article
  &image_url=https://www.rasulkireev.com/_astro/a_smiling_boy_from_Pixars_Coco.DrP3G0Ol.png
```

### Logo Style

Logo style is super useful if you are trying to highlight a company or a project, advertize job postings or anything like. Super minimalistic.

Here is how I use it for one of my job boards:

![Logo OG Image Example](https://osig.app/static/vendors/images/logo-example.818309c1b90d.png)

This is the that I use to generate the image:

```
https://osig.app/g?
  site=x
  &style=logo
  &font=markerfelt
  &title=Narrative
  &subtitle=Founding Senior Software Engineer
  &image_url=http://res.cloudinary.com/built-with-django/image/upload/v1728024021/user-profile-image-prod/hhxfplsthiaytuttoamc.jpg
```

## Fonts

*   Helvetica ![Helvetica Font Example](https://osig.app/static/vendors/images/helvetica-example.9d748f0e4cd3.png)
*   Markerfelt ![Markerfelt Font Example](https://osig.app/static/vendors/images/markerfelt-example.f0edc54d9ba4.png)
*   Papyrus ![Papyrus Font Example](https://osig.app/static/vendors/images/papyrus-example.03867e8bc712.png)

## Precautions

Once you insert this link on your site, make sure to test it before sharing links online. I like to use [this Twitter Card Validator](https://threadcreator.com/tools/twitter-card-validator)

## Notes

*   Subtitle text is truncated to 150 characters if longer.
*   You can remove the watermark by subscribing to the [PRO version](/pricing).

## Integrating into your Site

As people use this, I will start adding more specific instructions on how to add these to your specific site that might use different technologies:

*   Wordpress
*   Django
*   Astro
*   Ruby on Rails
*   Next.js
*   etc.

## API

I will be adding more instruction on how you can generate those images programmatically via an API soon.
