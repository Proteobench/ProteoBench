####################################
Reviewing a submitted benchmark run
####################################

Reference for maintainers reviewing a pull request that submits a new benchmark run. If you are
the one submitting a run rather than reviewing one, see
:doc:`../your-first-submission/index` instead — step 6 of that page summarizes what to expect
from review.

1. Go to the PR page on Proteobot.

2. Check the user's comments for any warning or information left for the reviewer.

3. Check the detected parameter changes. If empty fields were filled in manually because they
   weren't in the parameter file, that's fine. If a value was changed, it should be justified.

4. Check the 'Files Changed' tab for whether the parameter values look reasonable. If you notice a
   possible error in parameter parsing or metric calculation, contact the dev team.

5. Check that the submitted data is present on the server by clicking the link in the PR. Points
   submitted from local installs should not be accepted, since the data won't be present on the
   server.

6. If everything looks good and the PR is ready to be accepted:

   * Press 'Merge pull request'.
   * Confirm the merge.
   * Go to the 'Code' page.
   * Sync the fork.
   * Click 'Contribute' and open a pull request.

7. Go to the ProteoBench GitHub repository corresponding to the module's results and accept
   (merge) that pull request.
