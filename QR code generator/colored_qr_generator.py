import json
import qrcode
from PIL import Image

def load_node_colors(json_path):
    with open(json_path, 'r') as file:
        data = json.load(file)
    return data

def generate_colored_qr(node_id, color, output_folder="qr_codes"):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(node_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color="white")

    # Save image
    import os
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    filename = f"{output_folder}/qr_{node_id}.png"
    img.save(filename)
    print(f"Saved QR code for node '{node_id}' with color '{color}' as {filename}")

def main():
    json_path = "qr_codes.json"
    node_colors = load_node_colors(json_path)

    for node_id, props in node_colors.items():
        color = props.get("color", "black")  # default black if no color
        generate_colored_qr(node_id, color)

if __name__ == "__main__":
    main()
