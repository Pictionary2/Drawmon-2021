from tbpp_model import TBPP512_dense_separable
from matplotlib.patches import Polygon
from tbpp_utils import PriorUtil
import sys
from matplotlib import pyplot as plt
from data_pictText import ImageInputGenerator
import argparse
import json
from tqdm import tqdm

parser = argparse.ArgumentParser("visualise")
parser.add_argument("--data-path", type=str, dest="data_path", required=True)
parser.add_argument("--model-path", type=str, dest="model_path", required=True)
parser.add_argument("--batch-size", type=int, dest="batch_size", default=1)
parser.add_argument("--output-path", type=str, dest="output_path", default="./renders")
args = parser.parse_args()

model = TBPP512_dense_separable(
    input_shape=(512, 512, 1),
    softmax=True,
    scale=0.9,
    isQuads=False,
    isRbb=False,
    num_dense_segs=3,
    use_prev_feature_map=False,
    num_multi_scale_maps=5,
    num_classes=5,
    activation="tfa_mish",
)

model.load_weights(args.model_path)

prior_util = PriorUtil(model)

gen_val = ImageInputGenerator(
    args.data_path, args.batch_size, "val", give_idx=False
).get_dataset()


def minMaxTo4Coords(box):
    return [[box[0], box[1]], [box[0], box[3]], [box[2], box[3]], [box[2], box[1]]]


classes = ["bg", "text", "number", "symbol", "circle"]
colors = ["red", "#48f7ef", "green", "brown"]

for i, item in enumerate(tqdm(gen_val)):
    pred = model(item[0])

    boxes = prior_util.decode(
        pred[0].numpy(), class_idx=-1, confidence_threshold=0.4, fast_nms=False
    )

    for box in boxes:
        box_coords = minMaxTo4Coords(box[:4] * 511)
        p = Polygon(
            list(box_coords),
            closed=True,
            edgecolor=colors[int(box[-1] - 1)],
            facecolor="none",
            linewidth=3,
        )
        ax = plt.gca()
        ax.add_patch(p)

    plt.imshow(1 - item[0].numpy()[0, :, :, 0], cmap="gray")
    plt.axis("off")
    plt.savefig(f"{args.output_path}/{i}.png")
    plt.close()

    with open(f"{args.output_path}/{i}.txt", "w") as fil:
        json.dump(boxes.tolist(), fil)
