import torch
import torch.nn as nn
import os


class NoopModel(nn.Module):
    def __init__(self):
        super(NoopModel, self).__init__()
        self.func = torch.square

    def forward(self, x):
        return self.func(x)


def main():
    model_dir = os.path.join(os.path.dirname(__file__), "../../models")
    os.makedirs(model_dir, exist_ok=True)

    # Square model
    model_path = os.path.join(model_dir, "emulator.pt")
    print(f"[Python] Saving model to: {model_path}")

    model = NoopModel()
    model.eval()

    example_input = torch.randn(4, 3, dtype=torch.float64)
    traced = torch.jit.trace(model, example_input)
    traced.save(model_path)
    print("[Python] TorchScript Square model saved successfully.")

if __name__ == "__main__":
    main()