import argparse

from bs4 import BeautifulSoup
import json
import os
from ffmpeg import FFmpeg
from progress.bar import Bar
import requests
import shutil

from slugify import slugify


def download_image(download_path: str, url: str, file_name: str):
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(f"{download_path}/{file_name}.png", "wb") as f:
            shutil.copyfileobj(res.raw, f)


def gif_conversion(file_name: str, output_file: str):
    ffmpeg_script = (
        FFmpeg()
        .option("y")
        .input(file_name)
        .output(
            output_file,
            vf="split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            r=10,
            loop=0,
        )
    )
    ffmpeg_script.execute()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Pingu""")
    parser.add_argument(dest="url", type=str, help='Line url')
    parser.add_argument('-g', dest="is_github", help='Github Action', action='store_true')
    args = parser.parse_args()

    page = requests.get(args.url)
    soup = BeautifulSoup(page.content, "html.parser")
    title = "pingu" if args.is_github else slugify(soup.find("p", class_="mdCMN38Item01Ttl").text)
    stickers = soup.find_all("li", class_="mdCMN09Li")

    if len(stickers):
        path = f"stickers/{title}"
        os.makedirs(path, exist_ok=True)

        with Bar("Processing", max=len(stickers)) as bar:
            for sticker in stickers:
                sticker_attrs: dict = json.loads(sticker.attrs["data-preview"])
                sticker_id = sticker_attrs.get("id")
                sticker_url = (
                        sticker_attrs.get("animationUrl")
                        or sticker_attrs.get("popupUrl")
                        or sticker_attrs.get("staticUrl")
                )

                download_image(path, sticker_url, sticker_id)
                gif_conversion(f"{path}/{sticker_id}.png", f"{path}/{sticker_id}.gif")

                os.remove(f"{path}/{sticker_id}.png")
                bar.next()

        print(
            f"Done.\n"
            f'Please check the "{path}" folder.\n'
            f"Thank you for using Pingu 🐧"
        )

    else:
        print("Could not find stickers")
