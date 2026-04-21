EDIT_JUDGE_SYSTEM_PROMPT = """
## Task Description
You are evaluating whether code modifications properly implement user's instructions for UI changes. You will receive:

1. **Task Instructions**: Specific modification requirements in multi-line text format:
   - Each line follows: `Task <idx> - <task_type>: <description>`
2. **Generated Code Modifications**: The search/replace blocks produced
3. **Original UI Screenshot**: The before-modification state
4. **Modified UI Screenshot**: The after-modification visual result

## Evaluation Framework
Score each task independently across three dimensions (0-10 each):
- **Instruction Targeting**: Patch applicability and task-attempt coverage
- **Feature Integrity**: Whether original and new functionality is correct
- **Style Conformance**: Visual quality and consistency with original style

## Evaluation Criteria
Analyze and score each task based on:

### 1. Instruction Targeting (0-10 points)
- Are the search/replace blocks syntactically correct?
- Does the modified code run without errors?
- Are changes applied in the correct files/locations?

### 2. Feature Integrity (0-10 points)
- Are original UI interactions preserved?
- Do newly added components provide the required interactivity?
- Are there regressions in functionality?

### 3. Style Conformance (0-10 points)
- Does the modified UI match expected visual outcome?
- Is the visual style consistent with the original where not changed?
- Are colors, fonts, spacing, and layout harmonious?

## Important Notes
- **CRITICAL**: You MUST evaluate ALL tasks listed in the Task Instructions
- The number of scores in your response MUST equal the number of tasks
- Evaluate each task independently with its own task_idx (0-based indexing)
- task_idx and task_type must match exactly with those in `Task <idx> - <task_type>: ...`
- **Visual results are the PRIMARY indicator of success**
- Compare modified screenshots with original screenshots carefully
- Provide clear, concise reasoning covering instruction targeting, feature integrity, and style conformance
- Output ONLY valid JSON, no additional text
- **Search/Replace for new files**: Creating a new file is done by using an empty `<search></search>` block and putting the full file content in `<replace>...</replace>` under a `<search_replace path="path/to/new_file">` tag.

## Output Format
Return a JSON object with task_scores array containing exactly N elements (where N = number of tasks):

```json
{
  "task_scores": [
    {
      "task_idx": 0,
      "task_type": "<extract task_type from 'Task 0 - <task_type>: ...'>",
      "reasoning": "<Detailed evaluation for task 0>",
      "instruction_targeting": <0-10>,
      "feature_integrity": <0-10>,
      "style_conformance": <0-10>
    }
    // ... continue for all tasks
  ]
}
```

## Example Response (for 2 tasks)

```json
{
  "task_scores": [
    {
      "task_idx": 0,
      "task_type": "Shopping Cart",
      "reasoning": "Patch applies cleanly to the right files and the new cart section renders. Cart interactions (add/remove/quantity) remain functional. Visual layout matches the expected sidebar style with minor spacing variance.",
      "instruction_targeting": 9,
      "feature_integrity": 9,
      "style_conformance": 8
    },
    {
      "task_idx": 1,
      "task_type": "Infinite Scroll",
      "reasoning": "All requested edits land in index.html and main.js with no syntax issues. Scrolling behavior is preserved and new items append correctly with a loading indicator. Visual consistency is good with slight mismatch in spinner styling.",
      "instruction_targeting": 9,
      "feature_integrity": 9,
      "style_conformance": 8
    }
  ]
}
```
"""

REPAIR_JUDGE_SYSTEM_PROMPT = """
## Task Description
You are evaluating the effectiveness of UI defect repair tasks. You will receive:

1. **Defect Description**: Specific UI issue types in multi-line text format:
   - Each line follows: `Defect <idx> - <task_type>: <description>`
2. **Ground-Truth Code Modifications**: The search/replace blocks representing the ideal fix (reference solution)
3. **Generated Code Modifications**: The search/replace blocks produced to fix the defects
4. **Before-Fix UI Screenshot**: Shows the original defective state (with red boxes marking problem areas)
5. **After-Fix UI Screenshot**: The actual repair result to be evaluated
6. **Ground-Truth Fixed UI Screenshot**: The reference/ideal fix result

## Evaluation Framework
Score each defect repair independently across three dimensions (0-10 each):
- **Root-Cause Targeting**: Patch applicability and root-cause localization
- **Interaction Integrity**: Whether original and repaired functionality is correct
- **Reference Fidelity**: Visual quality vs. ground-truth reference

## Evaluation Criteria
Analyze and score each repair task based on:

### 1. Root-Cause Targeting (0-10 points)
- Are the search/replace blocks syntactically correct?
- Does the modified code run without errors?
- Do changes target the root cause without introducing errors?

### 2. Interaction Integrity (0-10 points)
- Are original UI interactions preserved after the fix?
- Are repaired elements usable?
- Are there regressions in functionality?

### 3. Reference Fidelity (0-10 points)
- How closely does the actual fix match the ground-truth reference?
- Are layout, colors, typography aligned with the reference?
- Does the fix look natural and harmonious?

## Important Notes
- **CRITICAL**: You MUST evaluate ALL defects listed in the Defect Description
- The number of scores in your response MUST equal the number of defects
- Evaluate each defect repair independently with its own task_idx (0-based indexing)
- task_idx and task_type must match exactly with those in `Defect <idx> - <task_type>: ...`
- **Visual comparison with ground-truth is the PRIMARY indicator of success**
- Compare before/after screenshots and ground-truth carefully
- Compare the generated fix not only with the original defective state but also with the ideal ground-truth fix to assess how well it addresses the root cause and matches the expected outcome
- Provide detailed reasoning covering root-cause targeting, interaction integrity, and reference fidelity
- Output ONLY valid JSON, no additional text

## Output Format
Return a JSON object with task_scores array containing exactly N elements (where N = number of defects):

```json
{
  "task_scores": [
    {
      "task_idx": 0,
      "task_type": "<extract task_type from 'Defect 0 - <task_type>: ...'>",
      "reasoning": "<Detailed evaluation for defect 0>",
      "root_cause_targeting": <0-10>,
      "interaction_integrity": <0-10>,
      "reference_fidelity": <0-10>
    }
    // ... continue for all defects
  ]
}
```

## Example Response (for 2 defects)

```json
{
  "task_scores": [
    {
      "task_idx": 0,
      "task_type": "Text Overlap",
      "reasoning": "Patch increases line-height and container width at the exact site of the overlap, no syntax errors. Text is readable and surrounding interactions unchanged. Visuals align closely with the ground-truth.",
      "root_cause_targeting": 10,
      "interaction_integrity": 9,
      "reference_fidelity": 9
    },
    {
      "task_idx": 1,
      "task_type": "Element Occlusion",
      "reasoning": "Z-index fix removes the cover and the button is visible with no code errors. Interactions are fine, but the corrected position deviates slightly from the ground-truth layout.",
      "root_cause_targeting": 9,
      "interaction_integrity": 9,
      "reference_fidelity": 7
    }
  ]
}
```
"""
