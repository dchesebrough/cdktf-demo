# CDKTF Demo

This is a demo of using the Hashicorp CDKTF library to deploy a simple static website with Terraform to an AWS S3 bucket.

Requirements:
- Routable via DNS
- Be routable via HTTPS only
- Only allow traffic from your IP
- Be creatable via CDKTF IAC
- Include a deployment timestamp
- No ClickOps*

_* Note: I've built this demo assuming a Route53 top-level domain is already registered to the account with a valid SSL certificate in ACM and a hosted zone, so that is the only step that requires ClickOps. In theory, it's possible to register a domain using the [aws_route53domains_domain](https://registry.terraform.io/providers/hashicorp/aws/5.91.0/docs/resources/route53domains_domain) resource but I assumed that was out of the scope of this exercise._

Here, I'm demonstrating a pattern that's worked well for me in the past: setting up an S3 bucket that's fronted by a CloudFront distribution. For security, only the CloudFront distribution is accessible via the Web; IAM enforces that the bucket contents can only be accessed by the distribution.

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

This will create a credentials file under `~/.aws/`. The project is configured to use the `us-east-1` region.

By default, the bucket policy is configured to only allow traffic to the IP address specified in `main.py`. Fetch your [IP address](https://www.whatismyip.com) and replace it in the `access_ip_address` variable.

Install pip dependencies with:
```
pipenv install --dev
```

Run a linter with:
```
pipenv run ruff check --fix
```

Deploy the project with:

```
cdktf deploy
```

Once deployed, the website should be accessible at:

```
cdktfdemo.boredhusky.net
```

This deployment assumes you have a registered Route 53 domain name with a hosted zone set up already. These are not managed by this deployment. The top-level domain listed in this codebase is owned by my personal AWS account. You can replace it with a Route53 TLD that you own under your own AWS account using the input variables.

When done, tear down the stack with:

```
cdktf destroy
```

## Possible Extensions

* Create a back-end component that services XHR API requests from the website.
* Use remote state in an S3 bucket instead of local state.
* Enable a versioning policy on the S3 website bucket.
* Create the S3 bucket as a static website bucket.