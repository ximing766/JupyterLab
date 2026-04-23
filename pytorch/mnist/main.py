import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.optim.lr_scheduler import StepLR
import os

# --- Model Definition ---
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        # Simple CNN for MNIST
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output

def train(model, device, train_loader, optimizer, epoch):
    # Set model to training mode (enables Dropout, BatchNorm, etc.)
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        # Calculate Negative Log Likelihood loss
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % 100 == 0:
            print(f'Train Epoch: {epoch} [{batch_idx * len(data)}/{len(train_loader.dataset)} '
                  f'({100. * batch_idx / len(train_loader):.0f}%)]\tLoss: {loss.item():.6f}')

def test(model, device, test_loader):
    # Set model to evaluation mode (disables Dropout, BatchNorm, etc.)
    model.eval()
    test_loss = 0
    correct = 0
    # Disable gradient calculation to save memory and computation during inference
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    print(f'\nTest set: Average loss: {test_loss:.4f}, Accuracy: {correct}/{len(test_loader.dataset)} '
          f'({100. * correct / len(test_loader.dataset):.2f}%)\n')

def main():
    # Training settings
    batch_size = 64
    test_batch_size = 1000
    epochs = 5
    lr = 1.0
    gamma = 0.7
    # Check if NVIDIA GPU is available for acceleration
    use_cuda = torch.cuda.is_available()
    # Map model/data to GPU if available, otherwise use CPU
    device = torch.device("cuda" if use_cuda else "cpu")

    print(f"Using device: {device}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接出脚本所在目录下的 data 文件夹
    data_path = os.path.join(script_dir, 'data')
    model_path = os.path.join(script_dir, 'model')

    # Define data preprocessing pipeline
    transform = transforms.Compose([
        # Convert image to PyTorch Tensor (scale pixels to [0, 1])
        transforms.ToTensor(),
        # Normalize with MNIST mean (0.1307) and std (0.3081)
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    # Download and load MNIST dataset
    train_kwargs = {'batch_size': batch_size}
    test_kwargs = {'batch_size': test_batch_size}
    if use_cuda:
        cuda_kwargs = {'num_workers': 1, 'pin_memory': True, 'shuffle': True}
        train_kwargs.update(cuda_kwargs)
        test_kwargs.update(cuda_kwargs)

    dataset1 = datasets.MNIST(data_path, train=True, download=True, transform=transform)
    dataset2 = datasets.MNIST(data_path, train=False, transform=transform)
    train_loader = torch.utils.data.DataLoader(dataset1, **train_kwargs)
    test_loader = torch.utils.data.DataLoader(dataset2, **test_kwargs)

    # Instantiate model and move it to target device (GPU or CPU)
    model = Net().to(device)
    # Adadelta optimizer: adapts learning rate based on gradient history
    optimizer = optim.Adadelta(model.parameters(), lr=lr)

    # Scheduler to decrease learning rate every epoch by a factor of gamma
    scheduler = StepLR(optimizer, step_size=1, gamma=gamma)
    for epoch in range(1, epochs + 1):
        train(model, device, train_loader, optimizer, epoch)
        test(model, device, test_loader)
        scheduler.step()

    # --- Save Model ---
    pt_path = os.path.join(model_path, "mnist_model.pt")
    torch.save(model.state_dict(), pt_path)
    print(f"Model saved to {pt_path}")

    # --- Export to ONNX (for Jetson/TensorRT) ---
    onnx_path = os.path.join(model_path, "mnist_model.onnx")
    dummy_input = torch.randn(1, 1, 28, 28).to(device)
    torch.onnx.export(model, dummy_input, onnx_path, 
                      input_names=['input'], output_names=['output'],
                      dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}})
    print(f"Model exported to ONNX: {onnx_path}")

if __name__ == '__main__':
    main()
