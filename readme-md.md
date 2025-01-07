# Canvas QTI Quiz Converter

This tool converts a CSV file containing quiz questions into a QTI-formatted ZIP file that can be imported into Canvas LMS.

## Features

- Supports multiple question types:
  - Multiple Choice (MC)
  - True/False (TF)
  - Multiple Response (MR)
  - Fill in the Blank (FB)
  - Matching (MT)
  - Numerical (NU)
  - Essay (ES)
  - File Upload (FU)

## Requirements

- Python 3.6+
- No additional external libraries required (uses only Python standard library)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/canvas-qti-converter.git
cd canvas-qti-converter
```

## Usage

1. Create a CSV file named `questions.csv` following the format specified below
2. Run the script:
```bash
python convert_to_qti.py
```
3. Enter a quiz title when prompted
4. The script will generate a QTI-compatible ZIP file

### CSV Format

Your CSV file should contain one question per row with no header row. The format depends on the question type:

1. Multiple Choice (MC):
```
MC,,points,question,correct_answer,choice1,choice2,choice3,choice4,choice5
```

2. True/False (TF):
```
TF,,points,question,true/false
```

3. Multiple Response (MR):
```
MR,,points,question,1,2,4,choice1,choice2,choice3,choice4,choice5
```

4. Fill in the Blank (FB):
```
FB,,points,question,correct_answer
```

5. Matching (MT):
```
MT,,points,question,term1:def1,term2:def2,term3:def3
```

6. Numerical (NU):
```
NU,,points,question,correct_number
```

7. Essay (ES):
```
ES,,points,question
```

8. File Upload (FU):
```
FU,,points,question
```

### Example CSV Content

```csv
MC,,1,"What is 2+2?",1,"4","5","6","7",""
TF,,1,"The sky is blue",true
MR,,1,"Select all prime numbers",1,2,3,"2","3","4","5","6"
FB,,1,"The capital of France is ___","Paris"
```

## Importing to Canvas

1. Go to Canvas Course Settings
2. Click 'Import Course Content'
3. Choose 'QTI .zip file'
4. Select 'Create a new quiz'
5. Upload the generated ZIP file

## Development

The main script is `convert_to_qti.py`. It uses Python's built-in libraries:
- `xml.etree.ElementTree` for XML generation
- `csv` for reading the input file
- `zipfile` for creating the output package

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.