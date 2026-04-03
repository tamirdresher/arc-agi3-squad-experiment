// ARC-AGI-3 Informed Squad Configuration
// Experiment: Testing ARC-informed agent prompt contracts
// Reference: tamirdresher_microsoft/tamresearch1#2058
// Research: arXiv:2603.24621 (ARC-AGI-3 Technical Paper)

export const squadConfig = {
  name: "arc-agi3-squad-experiment",
  version: "1.0.0",
  description:
    "ARC-AGI-3 informed Squad configuration — four-pillar prompt contracts for agentic intelligence",

  // ─── Core Principle ────────────────────────────────────────────────────────
  // ARC-AGI-3 reveals that intelligence is *efficiency under novelty*, not mere
  // correctness. The RHAE metric scores (human_baseline / agent_actions)^2,
  // meaning brute-force correct answers score near zero.
  //
  // This config operationalizes ARC's four pillars as explicit behavioral
  // contracts injected into every agent prompt.
  // ───────────────────────────────────────────────────────────────────────────

  arcPromptContract: {
    description:
      "Four-phase behavioral contract derived from ARC-AGI-3 pillars",
    phases: {
      explore: {
        pillar: "Exploration",
        instruction:
          "Before acting, identify what information is missing or ambiguous. " +
          "Ask: 'What do I not yet know that I need?' List 1-3 exploration actions. " +
          "Do NOT proceed to execution until exploration is complete.",
        maxExplorationActions: 3,
      },
      model: {
        pillar: "World Modeling",
        instruction:
          "State your current understanding of the environment and task state. " +
          "What are the constraints? What are the success criteria? What could go wrong? " +
          "Write this as a compact world model that will be shared with downstream agents.",
        outputFormat: "structured list: [constraints], [success_criteria], [risks]",
      },
      goal: {
        pillar: "Goal Setting",
        instruction:
          "State the specific outcome you are targeting, in your own words. " +
          "Is this the right goal? Are there implicit objectives the requester may have " +
          "that are not stated explicitly? Check for implicit constraints.",
        implicitGoalCheck: true,
      },
      execute: {
        pillar: "Planning & Execution with Course-Correction",
        instruction:
          "Carry out the plan. After each major action, check: " +
          "'Does this match my world model? Do I need to update my understanding?' " +
          "If observations conflict with model, update the model before continuing.",
        maxRefinementCycles: 3,
        courseCorrect: true,
      },
    },
  },

  // ─── Agent Roster ──────────────────────────────────────────────────────────
  agents: {
    coordinator: {
      role: "Scaffolding Agent",
      description:
        "Runs tutorial-level scaffolding before any specialist engages. " +
        "Establishes shared world model: constraints, success criteria, unknowns. " +
        "Inspired by ARC-AGI-3 tutorial-level design principle.",
      alwaysFirst: true,
      outputs: ["world-model", "constraint-list", "success-criteria", "unknown-list"],
    },
    explorer: {
      role: "Exploration Specialist",
      description:
        "First-turn specialist. Sole job: identify missing information before execution. " +
        "Outputs an 'exploration report' consumed by all downstream agents. " +
        "Directly implements ARC Pillar 1 (Exploration).",
      outputs: ["exploration-report"],
      skipCondition: "simple-factual tasks with no ambiguity",
    },
    specialist: {
      role: "Domain Expert",
      description:
        "Existing squad agents (Data, B'Elanna, Seven, etc.) operating under ARC prompt contract. " +
        "Each receives coordinator world model + explorer report before executing. " +
        "Applies all four ARC phases in sequence.",
      inputs: ["world-model", "exploration-report"],
      promptContractRequired: true,
    },
    verifier: {
      role: "Refinement Agent",
      description:
        "Reviews specialist output against the world model. Flags mismatches. " +
        "Triggers refinement cycle if output conflicts with world model or implicit goals. " +
        "Implements generate → verify → refine loop from ARC Prize 2025 NVARC technique.",
      maxCycles: 3,
      triggers: ["model-mismatch", "implicit-goal-missed", "efficiency-too-low"],
    },
    scribe: {
      role: "Session Logger",
      description:
        "Records session, world model updates, action counts, and SHAE scores for analysis. " +
        "Required for scoring — logs must be parseable by scoring/compute-shae.py.",
      outputs: ["session-log", "action-count", "shae-score"],
    },
  },

  // ─── Scoring ───────────────────────────────────────────────────────────────
  scoring: {
    metric: "SHAE",
    description: "Squad Human Action Efficiency — analogous to ARC-AGI-3's RHAE",
    formula: "(human_baseline_actions / agent_actions)^2",
    humanBaselines: {
      "simple-factual": 3,
      "multi-step-technical": 8,
      "implicit-goal": 6,
    },
    thresholds: {
      excellent: 0.7,
      good: 0.5,
      acceptable: 0.3,
      bruteForce: 0.1,
    },
    taskVariants: ["familiar", "near-ood", "far-ood"],
  },

  // ─── Experiment Parameters ─────────────────────────────────────────────────
  experiment: {
    hypothesis:
      "Applying ARC-AGI-3's four pillars as explicit agent behavioral contracts will: " +
      "(1) reduce task completion steps by ≥30%, " +
      "(2) reduce hallucination rate on novel variants, " +
      "(3) improve correctness on multi-mechanic compositional tasks.",
    taskSuites: ["tasks/task-01-simple-factual.md", "tasks/task-02-multi-step-technical.md", "tasks/task-03-implicit-goal.md"],
    configurations: ["baseline", "arc-informed"],
    comparisons: [
      "action_count",
      "revision_rate",
      "novel_variant_accuracy",
      "propagation_correctness",
    ],
  },
};

export default squadConfig;
