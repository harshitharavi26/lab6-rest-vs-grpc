#!/usr/bin/env python3

import argparse
import base64
import random
import time

import grpc

import lab6_pb2
import lab6_pb2_grpc


def doAdd(stub, debug=False):
    reply = stub.Add(lab6_pb2.AddRequest(a=5, b=10))
    if debug:
        print("Response is", reply.sum)


def doRawImage(stub, debug=False):
    img = open('Flatirons_Winter_Sunrise_edit_2.jpg', 'rb').read()
    reply = stub.RawImage(lab6_pb2.RawImageRequest(img=img))
    if debug:
        print("Response is", reply.width, reply.height)


def doDotProduct(stub, debug=False):
    a = [random.random() for _ in range(100)]
    b = [random.random() for _ in range(100)]
    reply = stub.DotProduct(lab6_pb2.DotProductRequest(a=a, b=b))
    if debug:
        print("Response is", reply.dotproduct)


def doJsonImage(stub, debug=False):
    img = open('Flatirons_Winter_Sunrise_edit_2.jpg', 'rb').read()
    encoded = base64.b64encode(img).decode('utf-8')
    reply = stub.JsonImage(lab6_pb2.JsonImageRequest(img=encoded))
    if debug:
        print("Response is", reply.width, reply.height)


# ---------------------------------------------------------
# Parse command-line arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser(
    description='gRPC client for measuring server operations'
)
parser.add_argument('host', help='IP address or hostname of the gRPC server')
parser.add_argument('cmd',
                    choices=['add', 'rawImage', 'dotProduct', 'jsonImage'],
                    help='Operation to perform')
parser.add_argument('reps', type=int,
                    help='Number of repetitions for measurement')
parser.add_argument('-p', '--port', type=int, default=50051,
                    help='Server port (default: 50051)')
parser.add_argument('-d', '--debug', action='store_true',
                    help='Print the response from the server')
args = parser.parse_args()

addr = f"{args.host}:{args.port}"
print(f"Running {args.reps} reps against {addr}")

# ---------------------------------------------------------
# Create the channel ONCE and reuse it for every call
# ---------------------------------------------------------

options = [
    ('grpc.max_receive_message_length', 50 * 1024 * 1024),
    ('grpc.max_send_message_length', 50 * 1024 * 1024),
]
channel = grpc.insecure_channel(addr, options=options)
stub = lab6_pb2_grpc.Lab6Stub(channel)

operations = {
    'add': doAdd,
    'rawImage': doRawImage,
    'dotProduct': doDotProduct,
    'jsonImage': doJsonImage,
}
operation = operations[args.cmd]

start = time.perf_counter()

for _ in range(args.reps):
    operation(stub, debug=args.debug)

delta = ((time.perf_counter() - start) / args.reps) * 1000
print("Took", delta, "ms per operation")
