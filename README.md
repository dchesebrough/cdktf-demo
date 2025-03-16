# CDKTF Demo

This is a demo of using the Hashicorp CDKTF library to deploy a simple static website with Terraform to an AWS S3 bucket.

Requirements:
- Routable via DNS
- Be routable via HTTPS only
- Only allow traffic from your IP
- Be creatable via CDKTF IAC
- No ClickOps deployment

## Instructions

These instructions are compatible with macOS Sonoma. 

Install the `awscli`, `terraform` and `cdktf` dependencies with Homebrew.

```
brew install awscli terraform cdktf
```

This project requires an AWS account with an API key. Configure this with:

```
aws configure
```

This will create a credentials file under `~/.aws/`

By default, the bucket policy is configured to only allow traffic to the IP address specified in `main.py`. Fetch your [IP address](https://www.whatismyip.com) and replace it in the `ACCESS_IP_ADDRESS` variable.

Deploy the project with:

```
cdktf deploy
```

The website should be accessible at:

```
cdktfdemo.boredhusky.net
```

This TLD is owned by my personal AWS account. You can replace it with a Route53 TLD that you own under your own AWS account.

When done, tear down the stack with:

```
cdktf destroy
```

## Possible Extensions

* Creating a CloudFront distribution would add region-specific caching for faster load times. Ensure to invalidate the cache whenever uploading a new version of the website.
