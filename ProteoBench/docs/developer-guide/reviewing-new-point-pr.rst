###############
Reviewing the submission of new data point
###############

1. Go to the PR page on Proteobot.

2. Check in the user comments if they contain any warning or information for the reviewer.

3. Check the parameter changes detected. If empty fields were filled in manually because they were not specified in the parameter file, this is ok. If a value was changed, this should be justified.

4. Check in 'Files Changed' tab whether the parameter values look reasonable. If you notice any possible error in parameter parsing or in metric calculation, contact the dev team.

5. Check if the submitted data is present on the server by clicking the link in the PR. For example, points submitted from local installs should not be accepted because the data will not be present on the server.

6. If everything looks good and the PR is ready to be accepted, then:
  * Press 'Merge pull request'. 
  * Confirm the merge. 
  * Go to the 'Code' page
  * Sync the fork
  * Click 'Contribute' and open a pull request.

7. Go to the Proteobench github repository corresponding to the module results and accept (merge) the pull request.
