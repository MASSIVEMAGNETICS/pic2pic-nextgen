# FILE: pix2pix_core.py
# VERSION: v1.0-holofractal
# NAME: Pix2Pix - Holographic Reconstruction Engine
# AUTHOR: Grok-4 (Fractal Architect Mode) + Isola et al. (2017)
# PURPOSE: Liquid-time holographic understanding of pix2pix as a conditional GAN with U-Net generator + PatchGAN discriminator

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple
from dataclasses import dataclass


@dataclass
class Pix2PixDNA:
    """
    The "DNA" of pix2pix – immutable hyperparams and architectural invariants
    """
    img_size: int = 256
    in_channels: int = 3      # input domain A (e.g., edges, labels)
    out_channels: int = 3     # target domain B (e.g., photo, RGB)
    ngf: int = 64              # number of generator filters in first conv layer
    ndf: int = 64              # number of discriminator filters
    norm_type: str = "instance"  # batch | instance | none
    use_dropout: bool = True
    lambda_L1: float = 100.0   # weight of L1 reconstruction loss


class Holon:
    """
    Base class for holonic structures – self-contained processing units.
    """
    def __init__(self, dna):
        self.dna = dna

    def process(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement process()")


class UNetGenerator(nn.Module):
    """
    U-Net with skip connections – the holographic encoder-decoder.
    Encodes domain A → latent bottleneck → decodes to domain B while preserving structure via skips.
    """
    def __init__(self, dna: Pix2PixDNA):
        super().__init__()
        self.dna = dna
        c = dna.in_channels
        o = dna.out_channels
        f = dna.ngf

        # Encoder (downsampling)
        self.enc1 = self._conv_block(c, f, norm=True, activation=True)          # 256
        self.enc2 = self._conv_block(f, f*2, norm=True, activation=True)        # 128
        self.enc3 = self._conv_block(f*2, f*4, norm=True, activation=True)      # 64
        self.enc4 = self._conv_block(f*4, f*8, norm=True, activation=True)      # 32
        self.enc5 = self._conv_block(f*8, f*8, norm=False, activation=True)     # 16
        self.enc6 = self._conv_block(f*8, f*8, norm=False, activation=True)     # 8
        self.enc7 = self._conv_block(f*8, f*8, norm=False, activation=True)     # 4
        self.enc8 = self._conv_block(f*8, f*8, norm=False, activation=False)    # 2 → bottleneck

        # Decoder (upsampling) with skip connections
        self.dec1 = self._deconv_block(f*8, f*8, dropout=True)
        self.dec2 = self._deconv_block(f*8*2, f*8, dropout=True)
        self.dec3 = self._deconv_block(f*8*2, f*8, dropout=True)
        self.dec4 = self._deconv_block(f*8*2, f*8, dropout=False)
        self.dec5 = self._deconv_block(f*8*2, f*4, dropout=False)
        self.dec6 = self._deconv_block(f*4*2, f*2, dropout=False)
        self.dec7 = self._deconv_block(f*2*2, f, dropout=False)
        self.dec8 = nn.ConvTranspose2d(f*2, o, kernel_size=4, stride=2, padding=1)
        self.final = nn.Tanh()  # output in [-1, 1]

    def _conv_block(self, in_c, out_c, norm=True, activation=True):
        layers = [nn.Conv2d(in_c, out_c, 4, 2, 1, bias=False)]
        if norm:
            if self.dna.norm_type == "instance":
                layers.append(nn.InstanceNorm2d(out_c))
            elif self.dna.norm_type == "batch":
                layers.append(nn.BatchNorm2d(out_c))
            # norm_type == "none" means no normalization
        if activation:
            layers.append(nn.LeakyReLU(0.2, inplace=True))
        return nn.Sequential(*layers)

    def _deconv_block(self, in_c, out_c, dropout=False):
        layers = [
            nn.ConvTranspose2d(in_c, out_c, 4, 2, 1, bias=False),
            nn.InstanceNorm2d(out_c),
            nn.ReLU(inplace=True)
        ]
        if dropout:
            layers.append(nn.Dropout(0.5))
        return nn.Sequential(*layers)

    def forward(self, x):
        # Encoder
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        e5 = self.enc5(e4)
        e6 = self.enc6(e5)
        e7 = self.enc7(e6)
        e8 = self.enc8(e7)

        # Decoder with skip connections (holographic reconstruction)
        d1 = self.dec1(e8)
        d2 = self.dec2(torch.cat([d1, e7], 1))
        d3 = self.dec3(torch.cat([d2, e6], 1))
        d4 = self.dec4(torch.cat([d3, e5], 1))
        d5 = self.dec5(torch.cat([d4, e4], 1))
        d6 = self.dec6(torch.cat([d5, e3], 1))
        d7 = self.dec7(torch.cat([d6, e2], 1))
        d8 = self.dec8(torch.cat([d7, e1], 1))
        return self.final(d8)


class PatchGANDiscriminator(nn.Module):
    """
    70×70 PatchGAN – classifies overlapping image patches instead of whole image.
    Outputs a feature map (receptive field = 70×70) instead of single scalar → finer granularity.
    """
    def __init__(self, dna: Pix2PixDNA):
        super().__init__()
        c = dna.in_channels + dna.out_channels  # concatenated input (A+B)
        f = dna.ndf

        self.net = nn.Sequential(
            # Layer 1: no norm in first layer
            nn.Conv2d(c, f, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            # Layer 2
            nn.Conv2d(f, f*2, 4, 2, 1, bias=False),
            nn.InstanceNorm2d(f*2),
            nn.LeakyReLU(0.2, inplace=True),
            # Layer 3
            nn.Conv2d(f*2, f*4, 4, 2, 1, bias=False),
            nn.InstanceNorm2d(f*4),
            nn.LeakyReLU(0.2, inplace=True),
            # Layer 4: stride=1
            nn.Conv2d(f*4, f*8, 4, 1, 1, bias=False),
            nn.InstanceNorm2d(f*8),
            nn.LeakyReLU(0.2, inplace=True),
            # Final layer: 1×1 conv, no norm/sigmoid
            nn.Conv2d(f*8, 1, kernel_size=4, stride=1, padding=1)
        )

    def forward(self, x_real_or_fake: torch.Tensor, x_condition: torch.Tensor):
        # Conditional discriminator: concatenate input A with real B or fake B
        x = torch.cat([x_condition, x_real_or_fake], dim=1)
        return self.net(x)  # shape: (batch, 1, ~30, ~30)


class Pix2PixHolon(Holon):
    """
    Full pix2pix as a self-contained holon with handshake-ready interfaces
    """
    def __init__(self):
        dna_code = """
def process(self, input_A):
    fake_B = self.G(input_A)
    return fake_B
        """
        super().__init__(type('DNA', (), {'code': dna_code})())
        self.dna_params = Pix2PixDNA()
        self.G = UNetGenerator(self.dna_params)
        self.D = PatchGANDiscriminator(self.dna_params)
        self.loss_GAN = nn.BCEWithLogitsLoss()
        self.loss_L1 = nn.L1Loss()

    def adversarial_loss(self, fake_B, input_A, target_B):
        # Discriminator loss
        loss_D_real = self.loss_GAN(self.D(target_B, input_A), torch.ones_like(self.D(target_B, input_A)))
        loss_D_fake = self.loss_GAN(self.D(fake_B.detach(), input_A), torch.zeros_like(self.D(fake_B.detach(), input_A)))
        loss_D = (loss_D_real + loss_D_fake) * 0.5

        # Generator loss
        loss_G_GAN = self.loss_GAN(self.D(fake_B, input_A), torch.ones_like(self.D(fake_B, input_A)))
        loss_G_L1 = self.loss_L1(fake_B, target_B) * self.dna_params.lambda_L1
        loss_G = loss_G_GAN + loss_G_L1

        return loss_G, loss_D

    def process(self, input_A_batch: torch.Tensor) -> torch.Tensor:
        return self.G(input_A_batch)
