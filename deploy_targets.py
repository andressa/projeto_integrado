import deploy

class stage(deploy.SimpleTarget):
    GIT_REPOSITORY = 'git@github.com:andressa/projeto_integrado.git'
    GIT_BRANCH = 'stage'
    SERVER = 'cc_mining@harrison.twistsystems.com'
    DJANGO_DEPLOY_ENV = 'stage'

