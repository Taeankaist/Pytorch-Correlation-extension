from __future__ import division
from __future__ import print_function

import argparse
import time

import torch
from spatial_correlation_sampler import SpatialCorrelationSampler

TIME_SCALES = {'s': 1, 'ms': 1000, 'us': 1000000}

parser = argparse.ArgumentParser()
parser.add_argument('backend', choices=['cpu', 'cuda'], default='cuda')
parser.add_argument('-b', '--batch-size', type=int, default=16)
parser.add_argument('-k', '--kernel-size', type=int, default=3)
parser.add_argument('--patch', type=int, default=3)
parser.add_argument('--patch_dilation', type=int, default=2)
parser.add_argument('-c', '--channel', type=int, default=64)
parser.add_argument('--height', type=int, default=100)
parser.add_argument('-w', '--width', type=int, default=100)
parser.add_argument('-s', '--stride', type=int, default=2)
parser.add_argument('-p', '--pad', type=int, default=1)
parser.add_argument('--scale', choices=['s','ms','us'], default='us')
parser.add_argument('-r', '--runs', type=int, default=100)

args = parser.parse_args()

input1 = torch.randn(args.batch_size,
                     args.channel,
                     args.height,
                     args.width).to(torch.device(args.backend))
input2 = torch.randn(args.batch_size,
                     args.channel,
                     args.height,
                     args.width).to(torch.device(args.backend))
input1.requires_grad = True
input2.requires_grad = True

correlation_sampler = SpatialCorrelationSampler(
    args.kernel_size,
    args.patch,
    args.stride,
    args.pad,
    args.patch_dilation)

# Force CUDA initialization
output = correlation_sampler(input1, input2)
print(output.size())
output.mean().backward()
forward_min = float('inf')
forward_time = 0
backward_min = float('inf')
backward_time = 0
for _ in range(args.runs):
    correlation_sampler.zero_grad()

    start = time.time()
    output = correlation_sampler(input1, input2)
    elapsed = time.time() - start
    forward_min = min(forward_min, elapsed)
    forward_time += elapsed

    start = time.time()
    (output.mean()).backward()
    elapsed = time.time() - start
    backward_min = min(backward_min, elapsed)
    backward_time += elapsed

scale = TIME_SCALES[args.scale]
forward_min *= scale
backward_min *= scale
forward_average = forward_time / args.runs * scale
backward_average = backward_time / args.runs * scale

print('Forward: {0:.3f}/{1:.3f} {4} | Backward {2:.3f}/{3:.3f} {4}'.format(
    forward_min, forward_average, backward_min, backward_average,
    args.scale))
