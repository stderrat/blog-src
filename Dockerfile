FROM registry.access.redhat.com/ubi8/ubi:8.1

RUN yum --disableplugin=subscription-manager -y update \
  && yum --disableplugin=subscription-manager -y install git ruby \
  && yum --disableplugin=subscription-manager clean all

RUN gem install asciidoctor

# The Hugo version
ARG VERSION=0.87.0

ADD https://github.com/gohugoio/hugo/releases/download/v${VERSION}/hugo_${VERSION}_Linux-64bit.tar.gz /usr/local/bin/hugo.tar.gz
RUN tar -zxvf /usr/local/bin/hugo.tar.gz -C /usr/local/bin/ \
  && /usr/local/bin/hugo version
RUN rm  -f /usr/local/bin/hugo.tar.gz \
  && rm -rf /tmp/LICENSE.md \
  && rm -rf /tmp/README.md

RUN useradd -ms /bin/bash deployer
USER deployer
WORKDIR /home/deployer