# Review criteria

Apply these criteria to the work's actual purpose. They do not prescribe a project layout, language, estimator, or personal style.

## For every review

- Identify the objective, supplied requirements, scope, and evidence needed to judge success.
- Check assumptions and dependencies that could change the conclusion. Distinguish an observed problem from a question or proposed additional check.
- Trace inputs, operations, and outputs where relevant. Check reproducibility and the permitted use of data and services.
- Assess the documented project conventions rather than imposing the reviewer's preferences.

## For research analyses or analysis plans

- State the quantity to estimate or other research objective, population/sample, and comparison before judging the estimator.
- For causal claims, examine the identification strategy and its assumptions. A DAG is one way to represent those assumptions, not a universal prerequisite for all research.
- Match the method, outcome support, uncertainty calculation, missing-data treatment, and dependence structure to the question.
- For Bayesian methods, examine priors and predictive checks; for MCMC, assess convergence and simulation precision. Apply the corresponding diagnostics to frequentist or predictive methods instead of requiring Bayesian checks.
- For predictive evaluation, separate development from final testing and avoid information leakage. For simulation, distinguish known truth, scenario design, and Monte Carlo uncertainty.
- Evaluate sensitivity to consequential choices and preserve the distinction between planned and exploratory analyses.
- Keep scientific requirements distinct from execution status and task tracking. A reproducible calculation can still be inappropriate for its research question.

## Reporting

Support findings with specific evidence and explain their effect. Preserve uncertainty, confidentiality, and relevant limitations. A static review does not establish that code executes correctly or that results have been independently reproduced.
