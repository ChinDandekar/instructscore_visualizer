import json
import os
import string


def convert_log_to_json(file, src_lang, tgt_lang, memorable_name):
    new_file = file.split("/")[-2]
    outputs = []

    with open(file) as f:
        lines = f.readlines()
        for i,line in enumerate(lines):
            data = json.loads(line)
            outputs.append([data["prediction"], data["reference"]])
    
    ansJson = {"type": "text2text"}
    all_outputs = []
    for output in outputs:
        inputString = f"You are evaluating {src_lang}-to-{tgt_lang} Machine translation task. The correct translation is \"{output[1]}\". The model generated translation is \"{output[0]}\". Please identify all errors within each model output, up to a maximum of five. For each error, please give me the corresponding error type, major/minor label, error location of the model generated translation and explanation for the error. Major errors can confuse or mislead the reader due to significant change in meaning, while minor errors don't lead to loss of meaning but will be noticed."
        all_outputs.append({"input": inputString, "reference": output[1], "prediction": output[0]})

    ansJson["instances"] = all_outputs
    if not os.path.exists(f"{os.path.dirname(os.path.abspath(__file__))}/jobs/{memorable_name}"):
        os.mkdir(f"{os.path.dirname(os.path.abspath(__file__))}/jobs/{memorable_name}")
    json.dump(ansJson, open(f"{os.path.dirname(os.path.abspath(__file__))}/jobs/{memorable_name}/{new_file}.json", "w"), indent=2)
    return new_file
    

def create_and_exec_slurm(memorable_name, file_name, email):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/jobs/{memorable_name}/{memorable_name}_{file_name}.sh", "w") as f:
        f.write("#!/usr/bin/env bash\n\n\n" + 
                "#SBATCH --nodes=1\n" +
                "#SBATCH --ntasks=1\n" + 
                "#SBATCH --cpus-per-task=32\n" +
                "#SBATCH --mem=128GB\n" +
                "#SBATCH --gpus=1\n" + 
                "#SBATCH --partition=aries\n" + 
                "#SBATCH --time=5-2:34:56\n" +
                "#SBATCH --account=chinmay\n" +
                "#SBATCH --mail-type=ALL\n" +
                f"#SBATCH --mail-user={email}\n" +
                f"#SBATCH --output=/mnt/taurus/data1/chinmay/instructscore_visualizer/jobs/{memorable_name}/{memorable_name}_{file_name}_slurm_out.txt\n" + 
                f"#SBATCH --error=/mnt/taurus/data1/chinmay/instructscore_visualizer/jobs/{memorable_name}/{memorable_name}_{file_name}_slurm_err.txt")
        
        f.write("\n\n")
        f.write("export CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7\n")
        f.write(f'python {os.path.dirname(os.path.abspath(__file__))}/eval.py --file_name "/mnt/taurus/data1/chinmay/instructscore_visualizer/jobs/{memorable_name}/{file_name}.json" --memorable_name {memorable_name}')
    pid = os.fork()
    if pid==0:
        os.chdir(f"{os.path.dirname(os.path.abspath(__file__))}/jobs/{memorable_name}")
        os.system(f"sbatch {os.path.dirname(os.path.abspath(__file__))}/jobs/{memorable_name}/{memorable_name}_{file_name}.sh")
        os._exit(0)
    else:
        os.waitpid(pid, 0)
        return 0

def instructscore_to_dict(file):
    with open(file) as f:
        data = json.load(f)
        first_data = data[0]
        pred = first_data["prediction"]
        ref = first_data["reference"]
        pred_render_data = {}
        pred_parts = pred.split()
        pred_render_data = {}
        for part in pred_parts:
            pred_render_data[part] = "None"
        # return pred_render_data
        errors = first_data["problem"]
        num_errors = errors["num_errors"]
        for i in range(1, num_errors+1):
            error = errors["error" + str(i)]
            error_type = error["error_type"]
            error_scale = error["error_scale"]
            error_explanation = error["error_explanation"]
            error_location = error["error_location"].lower()
            for key in pred_render_data:
                for keys in pred_render_data:
                    cleaned_key = key.translate(str.maketrans("", "", string.punctuation))
                    cleaned_error_location = error_location.translate(str.maketrans("", "", string.punctuation))
                    if cleaned_key == cleaned_error_location:
                        pred_render_data[f"{key}"] = {
                            "error_type": error_type,
                            "error_scale": error_scale,
                            "error_explanation": error_explanation,
                            "error_location": error_location
                        }
        print(pred_render_data)
    render_data = {
        "prediction": pred_render_data,
        "reference": ref
    }
    return render_data