# CS3081 Cloud Computing Mini Project

## Project
Knowledge Distillation and Cloud Deployment of a Lightweight Command-Parsing Language Model

## Repository
https://github.com/imnehal360/cs3081-cloud-mini-project

## Overview
This project distills command-parsing behavior from the phi3.5 teacher model into a smaller Pythia-70M student model.

The student is deployed through a FastAPI service on Kubernetes using k3d, with automated CI and performance testing.

## Architecture
Command dataset → Teacher labeling → Data cleaning → Student fine-tuning → Evaluation → FastAPI → Docker → Kubernetes

## Training
- Teacher: phi3.5
- Student: EleutherAI/pythia-70m
- Training records: 1,500
- Epochs: 3
- Evaluation records: 100
- Training environment: Google Colab T4

## Evaluation

| Metric | Student v1 | Student v2 |
|---|---:|---:|
| JSON validity | 100% | 100% |
| Intent accuracy | 83% | 79% |
| Date accuracy | 80% | 80% |
| Time accuracy | 80% | 85% |
| Place accuracy | 79% | 79% |
| Full-frame accuracy | 40% | 39% |

## Performance
- Load-testing tool: Locust
- Concurrent users: 4
- Duration: 2 minutes
- Requests: 365
- Failures: 0
- Median latency: 1300 ms
- p95 latency: 2900 ms
- Throughput: 3.07 requests/second

## Model Artifacts
Trained models and checksums are published in GitHub Release `model-v1`.

## Running the Project
The GitHub Actions workflow `test-kubernetes.yml` builds the service container, creates a k3d cluster, deploys the application, performs Kubernetes checks, and cleans up the cluster.

The `ci.yml` workflow performs linting, API unit tests, model evaluation, quality-gate checks, and secret scanning.

The deployment exposes `/parse`, `/healthz`, and `/readyz`.

## Testing
The project includes:
- FastAPI unit tests
- Kubernetes deployment verification
- Rolling-update and rollback tests
- Pod recovery tests
- Load-balancing checks
- Locust performance testing
- Model evaluation with a 95% JSON-validity gate
- Subnet allocation and NACL simulation

## Networking
See `network/subnets.md` and `network/nacl.json`.

## Results
See the `results/` directory.

## Known Limitations
- Model training was performed using Google Colab rather than local hardware.
- Kubernetes infrastructure was tested on a GitHub Actions runner rather than the local Mac.
- Object-storage integration and some requested deployment experiments are incomplete.
- The student model has lower full-frame accuracy than individual field accuracy.
