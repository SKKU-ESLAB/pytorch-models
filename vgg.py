import torch
import torch.nn as nn
from collections import OrderedDict, defaultdict

class VGG(nn.Module):
  ARCH = [64, 128, 'M', 256, 256, 'M', 512, 512, 'M', 512, 512, 'M']

  def __init__(self, state_dict=None, quant=False) -> None:
    super().__init__()

    layers = []
    counts = defaultdict(int)

    self.quant = quant

    def add(name: str, layer: nn.Module) -> None:
      layers.append((f"{name}{counts[name]}", layer))
      counts[name] += 1

    in_channels = 3
    for x in self.ARCH:
      if x != 'M':
        # conv-bn-relu
        add("conv", nn.Conv2d(in_channels, x, 3, padding=1, bias=False))
        add("bn", nn.BatchNorm2d(x))
        add("relu", nn.ReLU(True))
        in_channels = x
      else:
        # maxpool
        add("pool", nn.MaxPool2d(2))

    self.backbone = nn.Sequential(OrderedDict(layers))
    self.classifier = nn.Linear(512, 10)

    self.state_dict = state_dict
    if state_dict is not None:
      self.recover_model()

  def forward(self, x: torch.Tensor) -> torch.Tensor:
    # backbone: [N, 3, 32, 32] => [N, 512, 2, 2]
    x = self.backbone(x)

    # avgpool: [N, 512, 2, 2] => [N, 512]
    if self.quant:
      x = x.view(x.shape[0], -1)
    else:
      x = x.mean([2, 3])

    # classifier: [N, 512] => [N, 10]
    x = self.classifier(x)
    return x
  
  def recover_model(self):
    if self.state_dict is not None:
      self.load_state_dict(self.state_dict)


def cifar10_vgg9_bn(pretrained=False, quant=False, **kwargs):
  if pretrained:
    state_dict = torch.hub.load_state_dict_from_url(
        'https://hanlab18.mit.edu/files/course/labs/vgg.cifar.pretrained.pth',
        map_location='cpu',
        progress=True)
    state_dict = state_dict['state_dict']
  else:
    state_dict = None
  model = VGG(state_dict, quant)
  return model
