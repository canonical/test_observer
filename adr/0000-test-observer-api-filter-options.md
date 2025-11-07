# Test Observer API Filter Parameter Design Pattern

## Context and Problem Statement

The Test Observer API needs to support filtering test results based on various attributes (issues, artefacts, families, test cases, users, etc.). For any filterable attribute, users need to be able to:
- Find test results that have specific values for that attribute
- Find test results that have any value for that attribute
- Find test results that have no value for that attribute  
- Get all test results regardless of that attribute

Using issues as an example, users need to:
- Find test results that have some issues from a list attached
- Find test results that have any issues attached
- Find test results that have no issues attached  
- Get all test results regardless of issue status

How should we design a consistent API parameter structure pattern to support all these use cases across all filterable attributes while maintaining clarity and avoiding confusing behavior?

## Considered Options

* **Option 1: Single parameter with mixed types** - Use one parameter per filterable attribute that accepts strings ("any", "none") or arrays of specific values
* **Option 2: List-only with null** - Use only an array parameter where `null` means no filter, `[]` means no values, and `[1,2,3]` means specific values
* **Option 3: Separate parameters** - Use two parameters per filterable attribute like `has_<attribute>` (boolean) and `<attribute>_ids` (array) to control filtering

## Decision Outcome

Chosen option: **Option 1: Single parameter with mixed types**, because it provides clear semantics for each use case while avoiding the complexity and confusion of multiple overlapping parameters.

### API Design Pattern

This pattern should be applied consistently to all filterable attributes in the Test Observer API:

```json
{
    "issues": "any",        // has any issue
    "issues": "none",       // has no issues
    "issues": [1, 2, 3],    // has any of these specific issues
    "issues": null,         // no issue filter (default)
    
    "artefacts": "any",     // has any artefact
    "artefacts": "none",    // has no artefacts
    "artefacts": [4, 5, 6], // has any of these specific artefacts
    "artefacts": null,      // no artefact filter (default)
    
    "families": "any",      // belongs to any family
    "families": "none",     // belongs to no family
    "families": ["focal", "jammy"], // belongs to any of these families
    "families": null        // no family filter (default)
}
```

### Consequences

* Good, because each filter case has a clear, unambiguous meaning across all filterable attributes
* Good, because it's a single parameter per attribute that handles all use cases
* Good, because string values ("any", "none") are self-documenting
* Good, because it avoids invalid parameter combinations that would exist with multiple parameters per attribute
* Good, because the default behavior (null) is explicit and safe for all attributes
* Good, because it provides a consistent pattern that developers can learn once and apply everywhere
* Good, because it scales well as new filterable attributes are added to the API
* Bad, because each parameter accepts different types (string, array, null) which may require more careful validation
* Bad, because it's slightly less conventional than purely array-based filtering
