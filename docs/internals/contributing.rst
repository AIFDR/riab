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

With the develop branch being the backbone default branch with the bleeding edge and master always a stable release.



Process for developers adding a new feature:
============================================

Create a feature branch
    * git checkout -b <name> [from branch]

Write new code and tests
    ...

Publish (if unfinished)
    * git push origin <name>

To keep branch up to date
    * git checkout <name>
    * git merge origin/master

When all tests pass, either merge into master
    * git checkout master
    * git merge --no-ff <name>
      (possibly resolve conflict and verify test suite runs)
    * git push

Or issue a pull request through github
    ..

To delete when branch is no longer needed
    * git push origin :<name>


