Coding conventions for Risiko:
==============================

* Coding must follow a style guide. In case of Python it is http://www.python.org/dev/peps/pep-0008 and using the command line tool pep8 to enforce this
* Adherence to regression/unit testing wherever possible
* Use of github for revision control, issue tracking and WIKI
* Simple deployment procedure i.e. automatic system configuration and installation of dependencies (at least for Ubuntu)
* Develop in the spirit of XP/Agile, i.e. frequent releases, continuous integration and iterative development. The master branch should always be assumed to represent a working demo with all tests passing.


Branching guide
===============

Risiko follows the branching model laid out in this paper:
http://nvie.com/posts/a-successful-git-branching-model

With the develop branch being the backbone default branch
with the bleeding edge and master always a stable release.



Process for developers adding a new feature:
============================================

Create a feature branch
    * git checkout -b <featurebranch> develop

Write new code and tests
    ...

Publish (if unfinished)
    * git push origin <featurebranch>

To keep branch up to date
    * git checkout <featurebranch>
    * git merge origin develop

When all tests pass, either merge into develop
    * git checkout develop
    * git merge --no-ff <featurebranch>
      (possibly resolve conflict and verify test suite runs)
    * git push

Or issue a pull request through github
    ..

To delete when branch is no longer needed
    * git push origin :<featurebranch>



Process for making a new release:
=================================

Create a release branch from the current development branch
    * git checkout -b <releasebranch> master

Start working on release specific development (such as bumping version number)
    ...

When ready, merge release into master effectively making it official
    * git checkout master
    * git merge --no-ff <releasebranch>
    * git tag -a <version number>

Update development branch
    * git checkout develop
    * git merge --no-ff <releasebranch>
    (resolve conflicts)

Delete development branch
    * git branch -d <releasebranch>
    or
    * git push origin :<releasebranch>


Process for making a hotfix on master
=====================================

Create a hotfix branch from master
    * git checkout -b <hotfixbranch> master

Start working on fix (including bumping minor version number)
    ...

When fixed, merge fix back into both master and develop
    * git checkout master
    * git merge --no-ff <hotfixbranch>
    * git tag -a <version number>
    * git checkout develop
    * git merge --no-ff <hotfixbranch>

Delete hotfix branch
    * git branch -d <hotfixbranch>
