import torch
print(torch.__version__)
print(f"CUDA 是否可用: {torch.cuda.is_available()}")
print(f"显卡名称: {torch.cuda.get_device_name(0)}")