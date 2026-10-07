import torch

from model import create_model


print("===================================")
print("        TESTING MODEL")
print("===================================")

# Create the RetinaGuard model
model = create_model(num_classes=5)

print("Model created successfully!")

# Create a fake batch of 4 fundus images
dummy_input = torch.randn(4, 3, 224, 224)

# Run the images through the model
with torch.no_grad():
    output = model(dummy_input)

print(f"Input shape:  {dummy_input.shape}")
print(f"Output shape: {output.shape}")

print("\nExpected output shape: torch.Size([4, 5])")

if output.shape == (4, 5):
    print("\n✅ Model is configured for 5 DR classes!")
else:
    print("\n❌ Unexpected output shape.")

print("===================================")
