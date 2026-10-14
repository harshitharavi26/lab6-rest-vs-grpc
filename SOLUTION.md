# Lab 6 Solution: REST vs gRPC

## Setup

- Client VM and local/same-zone server VMs: `e2-standard-2` in `us-west1-a`.
- Different-region server: `e2-standard-2` in `europe-west3-a` (Frankfurt).
- All tests were run from the same client VM, using internal IP addresses (10.x.y.z).
- Local: client and server on the same VM (`localhost`). Same-zone: server on a second VM in `us-west1-a`.
- Repetitions: 1000 for `add` and `dotProduct` (100 across regions), 100 for image calls.
- The image is a 1.6 MB JPG (3004 x 1002). Each call reads the file and, for `jsonimg`, base64-encodes it.
- All values are milliseconds per call.

## Results

| Method | Local | Same-Zone | Different Region |
|--- |--- |--- |--- |
| REST add | 2.64 | 3.55 | 336.9 |
| gRPC add | 0.80 | 1.22 | 164.4 |
| REST rawimg | 5.54 | 8.06 | 1337.3 |
| gRPC rawimg | 10.12 | 11.63 | 184.0 |
| REST dotproduct | 3.10 | 3.84 | 327.2 |
| gRPC dotproduct | 0.97 | 1.29 | 166.0 |
| REST jsonimg | 27.49 | 31.35 | 1445.7 |
| gRPC jsonimg | 28.27 | 30.19 | 221.3 |
| PING | 0.051 | 0.391 | 158.8 |

Notes on how the numbers were chosen: local `rawimg` and same-zone image rows are medians of three runs.
Cross-region `add` and `dotproduct` are medians of three 100-rep runs. Local `jsonimg` and the
cross-region image rows are single runs. Cross-region results varied from run to run (for example,
gRPC `add` ranged from 146 to 183 ms), so those values are approximate.

## Observations

For small calls (`add`, `dotproduct`), gRPC was about 3x faster than REST on localhost and in the same
zone, and about 2x faster across regions. I think the main reason is connection handling: my gRPC
client creates one channel and reuses it for every call, while my REST client (`requests.post`) opens
a new TCP connection for each request. Across regions this is visible in the numbers: a REST `add`
took about 337 ms, roughly two ping round trips (2 x 159 ms), one to open the connection and one for
the request and response. A `curl` test showed the same pattern, with total time about twice the TCP
connect time. A gRPC `add` took about one round trip plus overhead. Protobuf's binary encoding is also
cheaper to produce and parse than JSON, which helps on small payloads.

For image calls on localhost and in the same zone, the two were close, and REST was faster for
`rawimg` (about 1.4x to 1.8x). I did not measure why; possible reasons are that gRPC splits a 1.6 MB
message into HTTP/2 frames and that Python protobuf copies the bytes. `jsonimg` was slower than `rawimg`
in both, because base64 makes the payload about 33% larger and adds encode and decode work on both ends.

Across regions, the image calls were much slower with REST (about 1.3 to 1.4 seconds) than with gRPC
(about 0.2 seconds). A likely cause is that every REST call opens a new TCP connection that has to
ramp up its sending rate before it can move 1.6 MB efficiently, while the gRPC connection stays open;
I did not verify this. Overall, call overhead dominates small calls, while payload size and network
distance dominate large ones, and ping shows the floor of about 159 ms between the two regions.
