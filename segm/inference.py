import warnings

import click
import torch
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
from tqdm import tqdm
from pathlib import Path
from PIL import Image
import numpy as np
import torchvision.transforms.functional as F

import segm.utils.torch as ptu

from segm.data.utils import STATS
from segm.data.ade20k import ADE20K_CATS_PATH
from segm.data.utils import dataset_cat_description, seg_to_rgb

from segm.model.factory import load_model
from segm.model.utils import inference


warnings.filterwarnings("ignore", category=DeprecationWarning)


@click.command()
@click.option("--model-path", type=str)
@click.option("--input-dir", "-i", type=str, help="folder with input images")
@click.option("--output-dir", "-o", type=str, help="folder with output images")
@click.option("--gpu/--cpu", default=True, is_flag=True)
@click.option("--legend", default=False, is_flag=True)
def main(model_path, input_dir, output_dir, gpu, legend):
    ptu.set_gpu_mode(gpu)

    model_dir = Path(model_path).parent
    model, variant = load_model(model_path)
    model.to(ptu.device)

    normalization_name = variant["dataset_kwargs"]["normalization"]
    normalization = STATS[normalization_name]
    cat_names, cat_colors = dataset_cat_description(ADE20K_CATS_PATH)

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    list_dir = list(input_dir.iterdir())
    for filename in tqdm(list_dir, ncols=80):
        pil_im = Image.open(filename).copy()
        im = F.pil_to_tensor(pil_im).float() / 255
        im = F.normalize(im, normalization["mean"], normalization["std"])
        im = im.to(ptu.device).unsqueeze(0)

        im_meta = dict(flip=False)
        logits = inference(
            model,
            [im],
            [im_meta],
            ori_shape=im.shape[2:4],
            window_size=variant["inference_kwargs"]["window_size"],
            window_stride=variant["inference_kwargs"]["window_stride"],
            batch_size=2,
        )
        seg_map = logits.argmax(0, keepdim=True)
        seg_rgb = seg_to_rgb(seg_map, cat_colors)
        seg_rgb = (255 * seg_rgb.cpu().numpy()).astype(np.uint8)
        pil_seg = Image.fromarray(seg_rgb[0])

        pil_blend = Image.blend(pil_im, pil_seg, 0.5).convert("RGB")

        # custom code to add the legend to the image
        if legend:
            label_to_color: dict[str, tuple] = {}
            classes = torch.unique(seg_map)
            for cls_color, cls_name in zip(classes, cat_names):
                # get color for class
                color = cat_colors[int(cls_color)]
                if len(color.shape) > 1:
                    color = color[0]
                label_to_color[cls_name] = color

            # Create a figure
            fig, ax = plt.subplots(figsize=(10, 8))

            # Display the image
            ax.imshow(np.array(pil_blend))
            ax.axis("off")

            # Create the legend
            handles = [
                mpatches.Patch(color=np.array(color), label=label)
                for label, color in label_to_color.items()
            ]
            ax.legend(
                handles=handles,
                loc="lower right",
                title="Legend",
                frameon=True,
                fontsize="medium",
                title_fontsize="large"
            )

            plt.savefig(output_dir / filename.name, bbox_inches="tight", pad_inches=0.2, dpi=300)
            plt.close()
        else:
            pil_blend.save(output_dir / filename.name)


if __name__ == "__main__":
    main()
