# Flux 1.1 Pro functionality for modifying images in Open WebUI


> The plugin's development has been temporarily suspended, its functionality is not guaranteed.

## Overview

This Python plugin integrates the **Black Forest Labs FLUX** inpainting API into the Open WebUI platform. It enables users to perform advanced image inpainting by selecting specific areas of an image, providing textual prompts, and generating high-quality edited images seamlessly within the Open WebUI environment.

## Features

- **Inpainting Support**: Allows users to select regions of an image and apply inpainting to modify or enhance specific areas based on textual prompts.
- **Change any picture**: The Load button in the inpainting interface allows you to load ANY image and change it!
- **Brush settings**: Adjust the size and softness of the brush for more precise inpainting.
- **Interactive HTML Interface**: Provides a user-friendly HTML interface within the chat for selecting mask areas and entering prompts, enhancing the inpainting workflow.
- **Customizable Parameters**: Enables configuration of inpainting steps, guidance scale, safety tolerance, output format, polling intervals, and maximum polling attempts.
- **Result Polling**: Automatically polls the FLUX API until the inpainting task is completed, ensuring users receive results promptly.
- **Saving Results Locally**: Downloads and stores generated images locally in the server’s cache directory, allowing for quick access and display within the chat without relying on external URLs.
- **Error Handling**: Implements comprehensive error handling for API request failures, polling timeouts, and input validation errors, ensuring robust and reliable operation.
- **Debugging Support**: Includes debug mode for detailed logging during development and troubleshooting.

## Requirements

**Python Libraries**:

- `asyncio`
- `re`
- `os`
- `json`
- `time`
- `base64`
- `uuid`
- `requests`
- `mimetypes`
- `pydantic`
- `typing`
- `pathlib`

Ensure these libraries are installed in your Python environment.

## Usage

### Function Integration

1. **Add the Plugin**: Place the plugin code in the Open WebUI feature catalog manually or use the designated integration method provided by Open WebUI.
2. **Configure Parameters**: Customize the inpainting parameters through the `Valves` class in the plugin code or via the Open WebUI interface.

### Parameter Entry

The following parameters are customizable through the `Valves` class:

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `FLUX_API_URL` | `str` | `"https://api.bfl.ml/v1"` | Base URL for the FLUX API (without trailing slash). |
| `FLUX_API_KEY` | `str` | `"YOUR-FLUX-API-KEY"` | API key for authenticating with the FLUX API, passed in the `x-key` header. |
| `STEPS` | `int` | `50` | Number of generation iterations (steps) for the inpainting process. |
| `GUIDANCE` | `int` | `60` | Guidance scale intensity for the inpainting process. |
| `SAFETY_TOLERANCE` | `int` | `6` | Safety moderation tolerance level (0 = strictest, 6 = most lenient). |
| `OUTPUT_FORMAT` | `str` | `"jpeg"` | Format of the final output image (`jpeg` or `png`). |
| `POLL_INTERVAL` | `int` | `2` | Interval in seconds between polling requests to check the status of the inpainting task. |
| `MAX_POLL_ATTEMPTS` | `int` | `60` | Maximum number of polling attempts before timing out if the inpainting task is not completed. |

### Performing Inpainting

1. **Initiate Inpainting**:
  
  - Create an Open WebUI chat image using [Flux Gen](https://github.com/fovendor/FLUX-Gen) or another generation tool.
  - Click the inpainting button in the chat room below the image.
  - Enter a text prompt in English describing the desired changes in the selected area.

2. **Generate Inpainted Image**:
  
  - The plugin will send the source image, drawn mask and promt to the FLUX API.
  - It will poll the API for the task status until the inpainting is complete or a timeout occurs.
  - Once completed, the inpainted image will be downloaded, saved locally, and displayed within the chat.

3. **Interact with the HTML Interface**:
  
  - The plugin provides an interactive HTML interface for selecting mask areas and entering tooltips. This is implemented through an [artifact within Open WebUI](https://docs.openwebui.com/features/code-execution/artifacts/). If you close the artifact, you can find it in the chat context menu..
  - Use valves and several attempts at inpeinting to get good results.
  - Upload your own images to edit using the Load button in the Inpainting web interface.

### Saving Images

The FLUX API returns the URL of the generated image. The plugin downloads this image and saves it locally in the server’s cache directory (`~/open-webui/backend/data/cache/image/generations/`). This approach ensures that images are accessible directly from the local server, enhancing performance and reliability.

**Recommendation:** To view the image in its original uncompressed resolution, open it in a new browser tab.

## Error Handling

- **API Request Errors**: Handles failures in sending requests to the FLUX API, including network issues and invalid responses.
- **Polling Timeouts**: Raises a timeout error if the inpainting task does not complete within the specified number of polling attempts.
- **Input Validation Errors**: Validates input parameters and raises errors for invalid configurations or missing required fields.
- **Image Download Errors**: Catches and reports errors encountered while downloading the generated image from the provided URL.
  
## Backlog

1. After pressing the Send button and receiving the task ID for changing the image, the html code must be removed from the chat!
2. Добавьте поле выбора к артефакту со списком моделей закрашивания: Fill, Canny или Depth. При выборе различных моделей должны стать доступны определенные опции!
3. So that, just like in the Gen plugin, users can enter prompts in their native language without the help of broken English and translators.
4. To prevent generated images from being part of one long assistant message, each generation should be placed in a separate "children" for the chat or in a new assistant message.
5. Move the STEPS, GUIDANCE and OUTPUT_FORMAT settings to an artifact so that the user can easily change the settings for each image.
6. Add the ability to crop and expand an image in an artifact after it has been picked up from a chat or loaded using the Load button.

## License

This plugin is licensed under the MIT License.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, feel free to open an issue or submit a pull request. Please ensure that your contributions adhere to the project's coding standards and include appropriate documentation and tests.
