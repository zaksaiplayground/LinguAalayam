# LinguAalayam

```
1. gcloud config configurations list
2. gcloud config configurations create <NEW_ACCOUNT_NAME>
3. gcloud config configurations activate <NEW_ACCOUNT_NAME>
4. gcloud auth login
5. gcloud config set project <PROJECT_ID>

```



```
❯ gcloud compute instances create <INSTANCE_NAME> \
  --project=<PROJECT_ID> \
  --zone=europe-west4-c \
  --machine-type=n1-standard-8 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --maintenance-policy=TERMINATE \
  --boot-disk-size=150GB \
  --image-family=pytorch-latest-gpu \
  --image-project=deeplearning-platform-release \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```