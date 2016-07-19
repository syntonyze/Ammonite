#!/usr/bin/env python
import os
import subprocess
import json
import sys


is_master_commit = (
    os.environ['TRAVIS_PULL_REQUEST'] == "false" and
    os.environ['TRAVIS_BRANCH'] == "test"
)


def update_version():
    git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip()
    version_txt = """
        package ammonite
        object Constants{
          val version = "COMMIT-%s"
          val curlUrl = "https://git.io/vKwA8"
        }
    """ % git_hash

    open("project/Constants.scala", "w").write(version_txt)


def publish_signed():
    creds = """
        (credentials in ThisBuild) += Credentials("Sonatype Nexus Repository Manager",
            "oss.sonatype.org",
            "%s",
            "%s"
        )
        pgpPassphrase := Some("%s".toArray)
        pgpSecretRing := file("secring.asc")
        pgpPublicRing := file("pubring.asc")
    """ % (
        os.environ['SONATYPE_DEPLOY_USER'],
        os.environ['SONATYPE_DEPLOY_PASSWORD'],
        os.environ['SONATYPE_PGP_PASSWORD']
    )
    open("sonatype.sbt", "w").write(creds)
    open("secring.asc", "w").write(
        json.loads('"' + os.environ['SONATYPE_PGP_KEY_CONTENTS'] + '"')
    )
    open("pubring.asc", "w").write(
        json.loads('"' + os.environ['SONATYPE_PGP_PUB_KEY_CONTENTS'] + '"')
    )
    subprocess.check_call([
        "sbt",
        "++2.10.5", "published/publishSigned",
        "++2.11.8", "published/publishSigned",
        "+amm/publishSigned",
        "+sshd/publishSigned"
    ])
    subprocess.check_call(["sbt", "sonatypeReleaseAll"])


def publish_docs():
    deploy_key = json.loads('"' + os.environ['DEPLOY_KEY'] + '"')
    with open("deploy_key", "w") as f:
        f.write(deploy_key)
    if os.environ.get("TRAVIS_TAG"):
        new_env = dict(os.environ, DOC_FOLDER=".")
    else:
        new_env = dict(os.environ, DOC_FOLDER="master")
    subprocess.check_call("ci/deploy_master_docs.sh", env=new_env)


if sys.argv[1] == "docs":
    if is_master_commit:
        update_version()
        publish_docs()
    else:
        subprocess.check_call(["sbt", "readme/run"])

elif sys.argv[1] == "artifacts":
    if is_master_commit:
        update_version()
        publish_signed()
    else:
        print "Not deploying artifacts since not a commit on master"
else:
    raise Exception("Unknown argument list %s" % sys.argv)