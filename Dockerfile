ARG DOCKER_REGISTRY=python
ARG PYTHON_VERSION=3.9
ARG DOCKER_IMAGE_VARIANT=slim-bookworm
FROM ${DOCKER_REGISTRY}:${PYTHON_VERSION}-${DOCKER_IMAGE_VARIANT} as base
ARG WORKSPACE_DIR=/workspace
WORKDIR ${WORKSPACE_DIR}/aimlops-dmle-meli-datapred-training-worker

# Change the default umask to grant write permissions to the group
RUN sed -ri 's/^#?UMASK\s+.*/UMASK 003/' /etc/login.defs

# Install the essential packages
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
        ca-certificates \
        build-essential \
        curl \
        git \
        openssh-client && \
    rm -rf /var/lib/apt/lists/*

# Setting the root dir of the virtual environment
ARG PDM_VERSION=2.16.1
RUN pip install --no-cache-dir pdm==${PDM_VERSION}
ENV VIRTUALENV_DIR /opt/virtualenv/envs
RUN mkdir -p ${VIRTUALENV_DIR} && chmod a+w ${VIRTUALENV_DIR}
RUN mkdir -p /etc/xdg/pdm && \
    echo "check_update = false" >> /etc/xdg/pdm/config.toml && \
    echo "[venv]\nlocation = \"${VIRTUALENV_DIR}\"" >> /etc/xdg/pdm/config.toml && \
    echo "[python]\nuse_venv = true" >> /etc/xdg/pdm/config.toml && \
    echo "[install]\ncache = false" >> /etc/xdg/pdm/config.toml

# Create a new virtual environment
ARG ENV_NAME=in-project
ENV PDM_IN_VENV=${ENV_NAME}
RUN pdm venv create -n ${ENV_NAME} ${PYTHON_VERSION}

# Install dependencies
COPY pyproject.toml pdm.lock pdm.sh README.md LICENSE ./
ARG ARTIFACTORY_PYPI_USER
RUN --mount=type=secret,id=artifactory_pypi_pass \
    ./pdm.sh sync --no-self && \
    pdm cache clear

# Activate the virtual environment on the next RUN commands
RUN pdm completion bash > /etc/bash_completion.d/pdm.bash-completion && \
    pdm completion zsh > /usr/share/zsh/vendor-completions/_pdm && \
    echo $(pdm venv activate ${PDM_IN_VENV}) >> ~/.bashrc

# Load the .bashrc file even on non-interactive shells
ENV BASH_ENV=~/.bashrc
SHELL ["/bin/bash", "-c"]

# Install as editable on the docker image
FROM base as prod

# Copy the source code and local configuration
COPY src src
COPY config config
# This is the version of the package
ARG PDM_BUILD_SCM_VERSION
# Install the package itself
RUN --mount=type=secret,id=artifactory_pypi_pass \
    ./pdm.sh sync && \
    pdm cache clear

FROM prod as testing
ARG CI=false
COPY config config
COPY tests tests
# Run tests during CI only
RUN --mount=type=secret,id=artifactory_pypi_pass \
    if [ "${CI}" = "true" ]; then \
    ./pdm.sh sync --no-self -dG test && \
    pdm run tests && \
    pdm cache clear ; \
    rm -rf tests config /root/.cache /tmp/* ; \
    fi

# Set the entrypoint as a login shell to load the ~/.profile
# The entrypoint script allows to use string without quotes as commands
RUN echo -e "#!/bin/bash\nexec bash -l -c \"\$*\"\n" > /etc/docker-entrypoint.sh
RUN chmod +x /etc/docker-entrypoint.sh
ENTRYPOINT ["/etc/docker-entrypoint.sh"]
CMD dmle_meli_datapred_training_worker


# Development layers
FROM base AS devel

# Additional tooling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-server \
        less \
        sudo \
        htop \
        vim \
        byobu \
        zsh && \
    rm -rf /var/lib/apt/lists/*


# Install additional development dependencies
ARG PDM_BUILD_SCM_VERSION
RUN --mount=type=secret,id=artifactory_pypi_pass \
    if [ -s pdm.lock ]; then \
    ./pdm.sh sync -dG:all && pdm cache clear; \
    else \
    echo "WARNING: pdm.lock not found. Skipping dev dependencies."; \
    fi

# Add local user to the image
ARG USERNAME=ainn
ARG GROUPNAME=ainn-sentrum
ARG USERUID=1001
ARG USERGID=1006
ARG USERSHELL=/bin/bash
RUN groupadd --gid ${USERGID} ${GROUPNAME} && \
    useradd -l -u ${USERUID} -g ${USERGID} -m ${USERNAME} -s ${USERSHELL} && \
    echo "umask 003" | tee -a /etc/profile.d/01-umask.sh

# SSH containers
FROM devel AS devel-ssh
EXPOSE 22
COPY docker-entrypoint.sh /etc/docker-entrypoint.sh
RUN chmod +x /etc/docker-entrypoint.sh
ENTRYPOINT ["/etc/docker-entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D"]

# DevContainers in Linux
FROM devel as devel-linux
ARG USERNAME=ainn
USER $USERNAME

# DevContainers in Windows
FROM devel-linux as devel-windows
ARG USERNAME=ainn
USER root
RUN mkdir -p /etc/sudoers.d && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME
USER $USERNAME
