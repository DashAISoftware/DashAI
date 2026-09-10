import React from "react";

export const experimentsTourSteps = [
  {
    target: "body",
    content: (
      <div>
        <h3>Experiments Module</h3>
        <p>
          Welcome to the Experiments module! This is where you train and compare
          machine learning models.
        </p>
        <p>Let's walk through creating your first experiment step by step.</p>
      </div>
    ),
    placement: "center",
    disableBeacon: true,
  },
  {
    target: '[data-tour="new-experiment-button"]',
    content: (
      <div>
        <h3>Start a New Experiment</h3>
        <p>
          Experiments let you train and compare several models on the same
          dataset.
        </p>
        <p>
          <strong>Click "New Experiment" to begin.</strong>
        </p>
      </div>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="experiment-name-input"]',
    content: (
      <div>
        <h3>Name Your Experiment</h3>
        <p>
          Here you can give to your experiment a descriptive name to help you
          identify it later.
        </p>
        <p>For now we will use the example name.</p>
      </div>
    ),
    placement: "bottom",
    spotlightClicks: true,
    disableBeacon: true,
  },
  {
    target: '[data-tour="exp-task-selector"]',
    content: (
      <div>
        <h3>Select the Task Type TabularClassification</h3>
        <p>Choose the type of machine learning task you want to perform:</p>
        <ul style={{ marginTop: "10px", marginBottom: "10px" }}>
          <li>
            <strong>TabularClassificationTask</strong> – for categorizing
            tabular data (we'll use this one)
          </li>
          <li>
            <strong>TextClassificationTask</strong> – for classifying text
            documents
          </li>
          <li>
            <strong>TranslationTask</strong> – for translating text between
            languages
          </li>
          <li>
            <strong>RegressionTask</strong> – for predicting continuous values
          </li>
        </ul>
        <p>
          <strong>Select "TabularClassificationTask" and click "Next".</strong>
        </p>
      </div>
    ),
    placement: "auto",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    styles: {
      tooltip: {
        width: "500px",
      },
      tooltipContent: {
        padding: "20px",
      },
    },
  },
  {
    target: '[data-tour="exp-task-selector-next-button"]',
    content: (
      <div>
        <h3>Continue to the Next Step</h3>
        <p>
          Once you have selected a task, click the "Next" button to proceed.
        </p>
      </div>
    ),
    placement: "auto",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-dataset-selector"]',
    content: (
      <div>
        <h3>Choose Your Dataset</h3>
        <p>Select the dataset you want to use for training your models.</p>
      </div>
    ),
    placement: "top",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-dataset-selector-next-button"]',
    content: (
      <div>
        <h3>Continue to the Next Step</h3>
        <p>
          Once you have selected a dataset, click the "Next" button to proceed.
        </p>
      </div>
    ),
    placement: "auto",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="dataset-input-columns-autocomplete"]',
    content: (
      <div>
        <h3>Define Input Columns</h3>
        <p>
          <strong>Input columns</strong> are the features your model will use to
          make predictions.
        </p>
        <p>
          These are the variables that contain information about each data
          point.
        </p>
        <p
          style={{
            backgroundColor: "rgba(44, 122, 255, 0.10)",
            borderLeft: "3px solid #2C7AFF",
            padding: "8px",
            borderRadius: "4px",
            marginTop: "10px",
          }}
        >
          💡 <strong>For this example:</strong> The input columns should already
          be pre-selected. They represent all the personality traits and
          demographic information.
        </p>
      </div>
    ),
    placement: "right",
    disableBeacon: true,
  },
  {
    target: '[data-tour="dataset-output-columns-autocomplete"]',
    content: (
      <div>
        <h3>Define Output Column</h3>
        <p>
          The <strong>output column</strong> is what your model will predict.
        </p>
        <p>
          This is also called the "target" or "label" – it's what you want the
          model to learn to predict.
        </p>
        <p
          style={{
            backgroundColor: "rgba(44, 122, 255, 0.10)",
            borderLeft: "3px solid #2C7AFF",
            padding: "8px",
            borderRadius: "4px",
            marginTop: "10px",
          }}
        >
          💡 <strong>Tip:</strong> The output column should already be selected.
          It represents the personality type we want to predict.
        </p>
      </div>
    ),
    placement: "right",
    disableBeacon: true,
  },
  {
    target: '[data-tour="exp-dataset-splits"]',
    content: (
      <div>
        <h3>Configure Data Splits</h3>
        <p>Machine learning models need data divided into three parts:</p>
        <ul style={{ marginTop: "10px", marginBottom: "10px" }}>
          <li>
            <strong>Training (60%)</strong> – used to teach the model
          </li>
          <li>
            <strong>Validation (20%)</strong> – used to tune the model
          </li>
          <li>
            <strong>Testing (20%)</strong> – used to evaluate final performance
          </li>
        </ul>
        <p>The default split of 60/20/20 works well for most cases.</p>
        <p>
          <strong>Keep the defaults.</strong>
        </p>
      </div>
    ),
    disableBeacon: true,
    spotlightClicks: true,
  },
  {
    target: '[data-tour="exp-prepare-dataset-next-button"]',
    content: (
      <div>
        <h3>Continue to the Next Step</h3>
        <p>
          Once you have prepared the dataset, click the "Next" button to
          proceed.
        </p>
      </div>
    ),
    placement: "auto",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: "body",
    content: (
      <div>
        <h3>Add Models to Compare</h3>
        <p>
          Experiments are designed for comparison, so you can train several
          models at once!
        </p>
        <p>
          Each model uses a different algorithm, which may perform differently
          on your data.
        </p>
        <p>Let's add three different models to compare their performance.</p>
      </div>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
  },
  {
    target: '[data-tour="exp-model-selector"]',
    content: (
      <div>
        <h3>Select Model Dropdown</h3>
        <p>
          <strong>Click on the dropdown</strong> to see the available models for
          your experiment.
        </p>
      </div>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-model-option-SVC"]',
    content: (
      <div>
        <h3>Select SVC Model</h3>
        <p>
          <strong>SVC (Support Vector Classifier)</strong> is a powerful
          algorithm that works well for complex classification tasks.
        </p>
        <p>
          It finds the optimal boundary between different classes in your data.
        </p>
        <p>
          <strong>Click on "SVC" to select it.</strong>
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-add-model-button"]',
    content: (
      <div>
        <h3>Add SVC to Experiment</h3>
        <p>The model name has been auto-filled for you.</p>
        <p>
          <strong>Click "Add"</strong> to include SVC in your experiment.
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-model-selector"]',
    content: (
      <div>
        <h3>Add Second Model</h3>
        <p>Great! Now let's add a different type of model to compare.</p>
        <p>
          <strong>Click the dropdown again</strong> to select another model.
        </p>
      </div>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-model-option-DecisionTreeClassifier"]',
    content: (
      <div>
        <h3>Select Decision Tree</h3>
        <p>
          <strong>DecisionTreeClassifier</strong> creates a tree-like model of
          decisions based on your data features.
        </p>
        <p>
          It's easy to interpret and works well with both numerical and
          categorical data.
        </p>
        <p>
          <strong>Click "DecisionTreeClassifier"</strong> to select it.
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-add-model-button"]',
    content: (
      <div>
        <h3>Add Decision Tree</h3>
        <p>
          <strong>Click "Add"</strong> to include the Decision Tree model in
          your experiment.
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-model-selector"]',
    content: (
      <div>
        <h3>Add Baseline Model</h3>
        <p>Finally, let's add a baseline model to compare against.</p>
        <p>
          <strong>Open the dropdown</strong> one more time.
        </p>
      </div>
    ),
    placement: "bottom",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-model-option-DummyClassifier"]',
    content: (
      <div>
        <h3>Select Dummy Classifier</h3>
        <p>
          <strong>DummyClassifier</strong> makes simple predictions without
          actually learning from the data.
        </p>
        <p>
          It serves as a baseline – if your other models don't perform better
          than this, they're not learning anything useful!
        </p>
        <p>
          <strong>Select "DummyClassifier".</strong>
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-add-model-button"]',
    content: (
      <div>
        <h3>Add Baseline Model</h3>
        <p>
          <strong>Click "Add"</strong> to include the Dummy Classifier as your
          baseline.
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },

  {
    target: '[data-tour="models-table"]',
    content: (
      <div>
        <h3>Your Models List</h3>
        <p>Here you can see all the models you've added to the experiment.</p>
        <p>
          You can edit model parameters by clicking the gear icon (⚙️) on each
          row. Also here you can use hyperparameter optimization to find the
          best settings automatically. But we'll skip that for now.
        </p>
        <p
          style={{
            backgroundColor: "rgba(251, 192, 45, 0.12)",
            borderLeft: "3px solid #fbc02d",
            padding: "8px",
            borderRadius: "4px",
            marginTop: "10px",
          }}
        >
          ⚠️ <strong>For this tutorial:</strong> We'll use the default
          parameters. Feel free to explore these settings later!
        </p>
        <p style={{ marginTop: "10px" }}>
          <strong>Click "Next" to proceed.</strong>
        </p>
      </div>
    ),
    placement: "top",
    disableBeacon: true,
    spotlightClicks: true,
    styles: {
      tooltip: {
        width: "500px",
      },
    },
  },
  {
    target: '[data-tour="exp-configure-models-next-button"]',
    content: (
      <div>
        <h3>Continue to the Next Step</h3>
        <p>
          Once you have added your models, click the "Next" button to proceed.
        </p>
      </div>
    ),
    placement: "auto",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="experiments-table"]',
    content: (
      <div>
        <h3>Experiment Created!</h3>
        <p>
          Great! Your experiment has been created and appears in the experiments
          table.
        </p>
        <p>
          Now let's run it to train all the models and see which performs best!
        </p>
      </div>
    ),
    placement: "top",
    disableBeacon: true,
  },
  {
    target: '[data-tour="exp-view-results-button"]',
    content: (
      <div>
        <h3>Run Your Experiment</h3>
        <p>
          Click the <strong>Eye Icon (👁️)</strong> to start training your
          models.
        </p>
        <p>
          This will open the results view where you can start the training
          process.
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="runner-dialog-start"]',
    content: (
      <div>
        <h3>Start Training</h3>
        <p>The Runner dialog shows you which models will be trained.</p>
        <p>
          <strong>Click "Start"</strong> to begin the training process.
        </p>
        <p
          style={{
            backgroundColor: "rgba(251, 192, 45, 0.12)",
            borderLeft: "3px solid #fbc02d",
            padding: "8px",
            borderRadius: "4px",
            marginTop: "10px",
            fontSize: "14px",
          }}
        >
          ⏱️ Training may take a few moments depending on your dataset size and
          models.
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
  },
  {
    target: '[data-tour="exp-results-metrics"]',
    content: (
      <div>
        <h3>Training in Progress</h3>
        <p>Watch as each model trains! You'll see:</p>
        <ul style={{ marginTop: "10px", marginBottom: "10px" }}>
          <li>✓ Checkmarks for completed models</li>
          <li>⏳ Progress indicators for models currently training</li>
          <li>📊 Real-time status updates</li>
        </ul>
        <p>Wait until all models finish training.</p>
      </div>
    ),
    disableBeacon: true,
    spotlightClicks: true,
    hideFooter: true,
    styles: {
      tooltip: {
        width: "500px",
      },
    },
  },
  {
    target: '[data-tour="results-table"]',
    content: (
      <div>
        <h3>View Your Results</h3>
        <p>
          Now that training is complete, let's see how your models performed!
        </p>
        <p>Each model is evaluated using several metrics:</p>
        <ul style={{ marginTop: "7px", marginBottom: "7px" }}>
          <li>
            <strong>Accuracy</strong> – overall correctness of predictions
          </li>
          <li>
            <strong>Precision</strong> – how many positive predictions were
            correct
          </li>
          <li>
            <strong>Recall</strong> – how many actual positives were found
          </li>
          <li>
            <strong>F1 Score</strong> – balance between precision and recall
          </li>
        </ul>
        <p>
          {" "}
          💡 <strong>Higher values</strong> (closer to 1.0 or 100%) generally
          indicate better performance!
        </p>
      </div>
    ),
    placement: "left",
    disableBeacon: true,
  },
  {
    target: '[data-tour="exp-results-view-tabs"]',
    content: (
      <div>
        <h3>Results Overview</h3>
        <p>
          The results view lets you analyze and compare your models'
          performance.
        </p>
        <p>You can switch between two views:</p>
        <ul style={{ marginTop: "10px", marginBottom: "10px" }}>
          <li>
            <strong>Columns</strong> – see metrics in a table format
          </li>
          <li>
            <strong>Graphs</strong> – visualize performance with charts
          </li>
        </ul>
      </div>
    ),
    placement: "bottom",
    disableBeacon: true,
  },
  {
    target: "body",
    content: (
      <div>
        <h3>🎉 Congratulations!</h3>
        <p>You've successfully completed the Experiments tutorial!</p>
        <hr style={{ margin: "15px 0", borderTop: "1px solid #ddd" }} />
        <h4>What You've Learned:</h4>
        <ul style={{ marginBottom: "15px" }}>
          <li>✓ How to create a new experiment</li>
          <li>✓ How to select and prepare your dataset</li>
          <li>✓ How to add and configure multiple models</li>
          <li>✓ How to train models and monitor progress</li>
          <li>✓ How to compare and evaluate model performance</li>
        </ul>
        <div
          style={{
            backgroundColor: "rgba(44, 122, 255, 0.08)",
            border: "1px solid rgba(44, 122, 255, 0.25)",
            borderRadius: "4px",
            padding: "12px",
            marginTop: "15px",
          }}
        >
          <p style={{ margin: "0", fontWeight: "bold", marginBottom: "8px" }}>
            🚀 Next Steps:
          </p>
          <ul style={{ margin: "0", paddingLeft: "20px" }}>
            <li>
              Try the <strong>Predictions</strong> module to use your trained
              models on new data
            </li>
            <li>
              Explore <strong>Explainability</strong> to understand what drives
              your models' decisions
            </li>
            <li>
              Experiment with different model parameters and hyperparameter
              optimization
            </li>
          </ul>
        </div>
      </div>
    ),
    placement: "center",
    disableBeacon: true,
    styles: {
      options: {
        zIndex: 2000,
      },
    },
    locale: {
      last: "Finish Tour",
    },
  },
];

export const experimentsTourConfig = {
  continuous: true,
  showProgress: true,
  showSkipButton: true,
  showBackButton: true,
  disableOverlayClose: false,
  disableCloseOnEsc: false,
};
