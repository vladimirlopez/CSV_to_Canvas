import csv
import uuid
import os
import zipfile
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

class CanvasQTIConverter:
    def __init__(self):
        self.ns = {
            'xmlns': "http://www.imsglobal.org/xsd/imsqti_v2p1",
            'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance"
        }
        self.question_types = {
            'MC': self.create_multiple_choice,
            'TF': self.create_true_false,
            'MR': self.create_multiple_response,
            'FB': self.create_fill_blank,
            'MT': self.create_matching,
            'NU': self.create_numerical,
            'ES': self.create_essay,
            'FU': self.create_file_upload
        }

    def prettify_xml(self, elem):
        """Return a pretty-printed XML string"""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def create_base_item(self, question_type, question_text, points):
        """Create base item structure common to all question types"""
        item = ET.Element('item')
        item.set('ident', f'question_{uuid.uuid4()}')
        item.set('title', question_text)
        
        itemmetadata = ET.SubElement(item, 'itemmetadata')
        qtimetadata = ET.SubElement(itemmetadata, 'qtimetadata')
        
        qtimetadatafield = ET.SubElement(qtimetadata, 'qtimetadatafield')
        fieldlabel = ET.SubElement(qtimetadatafield, 'fieldlabel')
        fieldlabel.text = 'question_type'
        fieldentry = ET.SubElement(qtimetadatafield, 'fieldentry')
        fieldentry.text = question_type
        
        qtimetadatafield = ET.SubElement(qtimetadata, 'qtimetadatafield')
        fieldlabel = ET.SubElement(qtimetadatafield, 'fieldlabel')
        fieldlabel.text = 'points_possible'
        fieldentry = ET.SubElement(qtimetadatafield, 'fieldentry')
        fieldentry.text = str(float(points))
        
        return item

    def create_multiple_choice(self, row_data):
        """Create a multiple choice question"""
        _, _, points, question_text, correct_answer, *choices = row_data
        choices = [c for c in choices if c.strip()]
        
        item = self.create_base_item('multiple_choice_question', question_text, points)
        
        presentation = ET.SubElement(item, 'presentation')
        material = ET.SubElement(presentation, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.text = question_text
        
        response_lid = ET.SubElement(presentation, 'response_lid')
        response_lid.set('ident', 'response1')
        response_lid.set('rcardinality', 'Single')
        
        render_choice = ET.SubElement(response_lid, 'render_choice')
        
        for i, choice in enumerate(choices, 1):
            response_label = ET.SubElement(render_choice, 'response_label')
            response_label.set('ident', str(i))
            material = ET.SubElement(response_label, 'material')
            mattext = ET.SubElement(material, 'mattext')
            mattext.text = choice
        
        resprocessing = ET.SubElement(item, 'resprocessing')
        outcomes = ET.SubElement(resprocessing, 'outcomes')
        decvar = ET.SubElement(outcomes, 'decvar')
        decvar.set('maxvalue', str(float(points)))
        decvar.set('minvalue', '0')
        decvar.set('varname', 'SCORE')
        decvar.set('vartype', 'Decimal')
        
        respcondition = ET.SubElement(resprocessing, 'respcondition')
        conditionvar = ET.SubElement(respcondition, 'conditionvar')
        varequal = ET.SubElement(conditionvar, 'varequal')
        varequal.set('respident', 'response1')
        try:
            varequal.text = str(int(correct_answer))
        except ValueError:
            varequal.text = correct_answer
        
        setvar = ET.SubElement(respcondition, 'setvar')
        setvar.set('varname', 'SCORE')
        setvar.set('action', 'Set')
        setvar.text = str(float(points))
        
        return item

    def create_true_false(self, row_data):
        """Create a true/false question"""
        _, _, points, question_text, correct_answer = row_data[:5]
        
        # Convert true/false to 1/2 for the multiple choice format
        correct_answer_num = '1' if str(correct_answer).lower().strip() == 'true' else '2'
        
        modified_row = [
            'MC', '', points, question_text, 
            correct_answer_num,
            'True', 'False'
        ]
        return self.create_multiple_choice(modified_row)

    def create_multiple_response(self, row_data):
        """Create a multiple response question"""
        _, _, points, question_text, correct_answers, *choices = row_data
        choices = [c for c in choices if c.strip()]
        
        item = self.create_base_item('multiple_answers_question', question_text, points)
        
        presentation = ET.SubElement(item, 'presentation')
        material = ET.SubElement(presentation, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.text = question_text
        
        response_lid = ET.SubElement(presentation, 'response_lid')
        response_lid.set('ident', 'response1')
        response_lid.set('rcardinality', 'Multiple')
        
        render_choice = ET.SubElement(response_lid, 'render_choice')
        
        for i, choice in enumerate(choices, 1):
            response_label = ET.SubElement(render_choice, 'response_label')
            response_label.set('ident', str(i))
            material = ET.SubElement(response_label, 'material')
            mattext = ET.SubElement(material, 'mattext')
            mattext.text = choice
        
        resprocessing = ET.SubElement(item, 'resprocessing')
        outcomes = ET.SubElement(resprocessing, 'outcomes')
        decvar = ET.SubElement(outcomes, 'decvar')
        decvar.set('maxvalue', str(float(points)))
        decvar.set('minvalue', '0')
        decvar.set('varname', 'SCORE')
        decvar.set('vartype', 'Decimal')
        
        correct_answers = [int(x.strip()) for x in str(correct_answers).split(',')]
        for answer in correct_answers:
            respcondition = ET.SubElement(resprocessing, 'respcondition')
            conditionvar = ET.SubElement(respcondition, 'conditionvar')
            varequal = ET.SubElement(conditionvar, 'varequal')
            varequal.set('respident', 'response1')
            varequal.text = str(answer)
            
            setvar = ET.SubElement(respcondition, 'setvar')
            setvar.set('varname', 'SCORE')
            setvar.set('action', 'Set')
            setvar.text = str(float(points) / len(correct_answers))
        
        return item

    def create_fill_blank(self, row_data):
        """Create a fill in the blank question"""
        _, _, points, question_text, correct_answer = row_data[:5]
        
        item = self.create_base_item('fill_in_the_blank_question', question_text, points)
        
        presentation = ET.SubElement(item, 'presentation')
        material = ET.SubElement(presentation, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.text = question_text
        
        response_str = ET.SubElement(presentation, 'response_str')
        response_str.set('ident', 'response1')
        response_str.set('rcardinality', 'Single')
        
        render_fib = ET.SubElement(response_str, 'render_fib')
        render_fib.set('rows', '1')
        render_fib.set('columns', '30')
        
        resprocessing = ET.SubElement(item, 'resprocessing')
        outcomes = ET.SubElement(resprocessing, 'outcomes')
        decvar = ET.SubElement(outcomes, 'decvar')
        decvar.set('maxvalue', str(float(points)))
        decvar.set('minvalue', '0')
        decvar.set('varname', 'SCORE')
        decvar.set('vartype', 'Decimal')
        
        respcondition = ET.SubElement(resprocessing, 'respcondition')
        conditionvar = ET.SubElement(respcondition, 'conditionvar')
        varequal = ET.SubElement(conditionvar, 'varequal')
        varequal.set('respident', 'response1')
        varequal.set('case', 'no')
        varequal.text = correct_answer
        
        setvar = ET.SubElement(respcondition, 'setvar')
        setvar.set('varname', 'SCORE')
        setvar.set('action', 'Set')
        setvar.text = str(float(points))
        
        return item
        
    def create_matching(self, row_data):
        """Create a matching question"""
        _, _, points, question_text, *pairs = row_data[:-1]  # Exclude empty last column
        pairs = [p for p in pairs if p.strip()]  # Remove empty pairs
        
        item = self.create_base_item('matching_question', question_text, points)
        
        presentation = ET.SubElement(item, 'presentation')
        material = ET.SubElement(presentation, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.text = question_text
        
        # Add all answers in a fixed order
        all_answers = [pair.split(':', 1)[1].strip() for pair in pairs if ':' in pair]
        
        # Create response_lid for each question
        for i, pair in enumerate(pairs, 1):
            if ':' in pair:
                question_text, answer = pair.split(':', 1)
                
                response_lid = ET.SubElement(presentation, 'response_lid')
                response_lid.set('ident', f'response_{i}')
                
                material = ET.SubElement(response_lid, 'material')
                mattext = ET.SubElement(material, 'mattext')
                mattext.text = question_text.strip()
                
                render_choice = ET.SubElement(response_lid, 'render_choice')
                
                # Add all possible answers
                for j, possible_answer in enumerate(all_answers, 1):
                    response_label = ET.SubElement(render_choice, 'response_label')
                    response_label.set('ident', str(j))
                    material = ET.SubElement(response_label, 'material')
                    mattext = ET.SubElement(material, 'mattext')
                    mattext.text = possible_answer
        
        # Response processing
        resprocessing = ET.SubElement(item, 'resprocessing')
        outcomes = ET.SubElement(resprocessing, 'outcomes')
        decvar = ET.SubElement(outcomes, 'decvar')
        decvar.set('maxvalue', str(float(points)))
        decvar.set('minvalue', '0')
        decvar.set('varname', 'SCORE')
        decvar.set('vartype', 'Decimal')
        
        # Add conditions for correct matches
        for i, pair in enumerate(pairs, 1):
            if ':' in pair:
                question_text, answer = pair.split(':', 1)
                correct_index = all_answers.index(answer.strip()) + 1
                
                respcondition = ET.SubElement(resprocessing, 'respcondition')
                conditionvar = ET.SubElement(respcondition, 'conditionvar')
                varequal = ET.SubElement(conditionvar, 'varequal')
                varequal.set('respident', f'response_{i}')
                varequal.text = str(correct_index)
                
                setvar = ET.SubElement(respcondition, 'setvar')
                setvar.set('varname', 'SCORE')
                setvar.set('action', 'Set')
                setvar.text = str(float(points) / len(pairs))
        
        return item

    def create_numerical(self, row_data):
        """Create a numerical question"""
        _, _, points, question_text, correct_answer = row_data[:5]
        
        item = self.create_base_item('numerical_question', question_text, points)
        
        presentation = ET.SubElement(item, 'presentation')
        material = ET.SubElement(presentation, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.text = question_text
        
        response_str = ET.SubElement(presentation, 'response_str')
        response_str.set('ident', 'response1')
        response_str.set('rcardinality', 'Single')
        
        render_fib = ET.SubElement(response_str, 'render_fib')
        render_fib.set('rows', '1')
        render_fib.set('columns', '10')
        
        resprocessing = ET.SubElement(item, 'resprocessing')
        outcomes = ET.SubElement(resprocessing, 'outcomes')
        decvar = ET.SubElement(outcomes, 'decvar')
        decvar.set('maxvalue', str(float(points)))
        decvar.set('minvalue', '0')
        decvar.set('varname', 'SCORE')
        decvar.set('vartype', 'Decimal')
        
        respcondition = ET.SubElement(resprocessing, 'respcondition')
        conditionvar = ET.SubElement(respcondition, 'conditionvar')
        varequal = ET.SubElement(conditionvar, 'varequal')
        varequal.set('respident', 'response1')
        varequal.text = str(float(correct_answer))
        
        setvar = ET.SubElement(respcondition, 'setvar')
        setvar.set('varname', 'SCORE')
        setvar.set('action', 'Set')
        setvar.text = str(float(points))
        
        return item

    def create_essay(self, row_data):
        """Create an essay question"""
        _, _, points, question_text = row_data[:4]
        
        item = self.create_base_item('essay_question', question_text, points)
        
        presentation = ET.SubElement(item, 'presentation')
        material = ET.SubElement(presentation, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.text = question_text
        
        response_str = ET.SubElement(presentation, 'response_str')
        response_str.set('ident', 'response1')
        response_str.set('rcardinality', 'Single')
        
        render_fib = ET.SubElement(response_str, 'render_fib')
        render_fib.set('rows', '5')
        render_fib.set('columns', '40')
        
        return item

    def create_file_upload(self, row_data):
        """Create a file upload question"""
        _, _, points, question_text = row_data[:4]
        
        item = self.create_base_item('file_upload_question', question_text, points)
        
        presentation = ET.SubElement(item, 'presentation')
        material = ET.SubElement(presentation, 'material')
        mattext = ET.SubElement(material, 'mattext')
        mattext.text = question_text
        
        response_str = ET.SubElement(presentation, 'response_str')
        response_str.set('ident', 'response1')
        response_str.set('rcardinality', 'Single')
        
        return item

    def create_assessment(self, quiz_title, questions):
        """Create a basic assessment structure"""
        assessment = ET.Element('questestinterop')
        
        assessment_meta = ET.SubElement(assessment, 'assessment')
        assessment_meta.set('title', quiz_title)
        assessment_meta.set('ident', f'assessment_{uuid.uuid4()}')
        
        section = ET.SubElement(assessment_meta, 'section')
        section.set('ident', 'root_section')
        
        for q in questions:
            section.append(q)
        
        return assessment

    def convert_csv_to_qti(self, input_file, quiz_title="Imported Quiz", output_file=None):
        """Convert CSV file to QTI format"""
        if output_file is None:
            output_file = f'canvas_quiz_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        
        questions = []
        
        with open(input_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row or not row[0].strip():  # Skip empty rows
                    continue
                    
                question_type = row[0].upper()
                if question_type in self.question_types:
                    questions.append(self.question_types[question_type](row))
        
        assessment = self.create_assessment(quiz_title, questions)
        
        temp_dir = 'qti_temp'
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with open(os.path.join(temp_dir, 'assessment.xml'), 'w', encoding='utf-8') as f:
                f.write(self.prettify_xml(assessment))
            
            with zipfile.ZipFile(output_file, 'w') as zf:
                zf.write(os.path.join(temp_dir, 'assessment.xml'), 'assessment.xml')
            
            return output_file
            
        finally:
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, file))
                os.rmdir(temp_dir)


if __name__ == "__main__":
    converter = CanvasQTIConverter()
    
    if not os.path.exists('questions.csv'):
        print("Error: questions.csv not found in the current directory")
        print("\nYour CSV file should follow this format (no header row):")
        print("\nQuestion Types and Formats:")
        print("1. Multiple Choice (MC):")
        print("   MC,,points,question,correct_answer,choice1,choice2,choice3,choice4,choice5")
        print("\n2. True/False (TF):")
        print("   TF,,points,question,true/false")
        print("\n3. Multiple Response (MR):")
        print("   MR,,points,question,1,2,4,choice1,choice2,choice3,choice4,choice5")
        print("\n4. Fill in the Blank (FB):")
        print("   FB,,points,question,correct_answer")
        print("\n5. Matching (MT):")
        print("   MT,,points,question,term1:def1,term2:def2,term3:def3")
        print("\n6. Numerical (NU):")
        print("   NU,,points,question,correct_number")
        print("\n7. Essay (ES):")
        print("   ES,,points,question")
        print("\n8. File Upload (FU):")
        print("   FU,,points,question")
        print("\nExample row:")
        print('MC,,1,"What is 2+2?",1,"4","5","6","7",""')
        exit(1)
    
    try:
        quiz_title = input("Enter quiz title: ").strip() or "Imported Quiz"
        output_file = converter.convert_csv_to_qti('questions.csv', quiz_title)
        print(f"\nSuccessfully created QTI package: {output_file}")
        print("\nImport instructions:")
        print("1. Go to Canvas Course Settings")
        print("2. Click 'Import Course Content'")
        print("3. Choose 'QTI .zip file'")
        print("4. Select 'Create a new quiz'")
        print("5. Upload the generated ZIP file")
    except Exception as e:
        print(f"\nError creating QTI package: {str(e)}")