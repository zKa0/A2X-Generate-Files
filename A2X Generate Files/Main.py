import re
import json
import os
import glob

# Função para converter o nome das variáveis em formato adequado para C++
def convert_name(name):
    return name.replace("::", "_").replace(" ", "_").replace("-", "_")

# Função para gerar o conteúdo do .hpp (sem valores definidos)
def generate_hpp(structs):
    hpp_content = ""

    for struct_name, variables in structs.items():
        hpp_content += f"inline struct {convert_name(struct_name)}Offsets {{\n"
        for var_name in variables:
            hpp_content += f"\tDWORD {convert_name(var_name)};\n"
        hpp_content += f"}} {convert_name(struct_name)};\n\n"

    return hpp_content

# Função para ler offsets e valores do arquivo .hpp
def parse_cpp_offsets(file_path):
    offsets = {}
    current_namespace = None

    # Expressão regular para capturar o início da namespace
    namespace_pattern = re.compile(r'namespace\s+(\w+)\s*\{')
    # Expressão regular para capturar o nome da variável e o valor associado
    offset_pattern = re.compile(r'constexpr\s+std::ptrdiff_t\s+(\w+)\s*=\s*(0x[0-9a-fA-F]+);')

    # Abrir e ler o arquivo .hpp
    with open(file_path, 'r', encoding='utf-8') as cpp_file:
        content = cpp_file.readlines()

        # Processar o conteúdo linha por linha
        for line in content:
            # Verificar se a linha contém a definição de uma namespace
            namespace_match = namespace_pattern.search(line)
            if namespace_match:
                current_namespace = namespace_match.group(1)
                if current_namespace not in offsets:
                    offsets[current_namespace] = {}

            # Verificar se a linha contém uma definição de variável com valor
            offset_match = offset_pattern.search(line)
            if offset_match and current_namespace:
                var_name = offset_match.group(1)
                var_value = offset_match.group(2)
                offsets[current_namespace][var_name] = var_value  # Adiciona o valor real da variável

    # Remove namespaces que não possuem variáveis
    offsets = {ns: vars for ns, vars in offsets.items() if vars}

    return offsets

# Função para salvar offsets em arquivo JSON
def save_offsets_to_json(offsets, output_file):
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(offsets, json_file, indent=4)

# Função para gerar código C++ para definir os offsets a partir do JSON no formato findOffsetByName
def generate_cpp_offset_code(json_file, output_cpp_file):
    print(f"[DEBUG] Gerando código C++ a partir do arquivo JSON: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    cpp_code = []

    # Percorre os namespaces no JSON
    for namespace, offsets in json_data.items():
        cpp_code.append(f"// Atribuições para {namespace}")
        cpp_code.append(f"// {namespace} Offsets")

        for var_name in offsets.keys():
            # Gera a linha no formato solicitado
            cpp_code.append(f'{namespace}.{convert_name(var_name)} = findOffsetByName(j, "{namespace}", "{var_name}");')

        cpp_code.append("")  # Adiciona uma linha em branco para separação

    # Grava o código gerado em um arquivo .cpp
    print(f"[DEBUG] Salvando o arquivo C++: {output_cpp_file}")
    with open(output_cpp_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(cpp_code))

# Função para processar todos os arquivos .hpp em um diretório
def process_all_cpp_files(directory):
    all_offsets = {}

    # Busca por todos os arquivos .hpp na pasta e subpastas
    cpp_files = glob.glob(os.path.join(directory, '**', '*.hpp'), recursive=True)

    for cpp_file in cpp_files:
        offsets = parse_cpp_offsets(cpp_file)

        # Combinar as offsets encontradas em todos os arquivos
        for namespace, namespace_offsets in offsets.items():
            if namespace not in all_offsets:
                all_offsets[namespace] = {}
            all_offsets[namespace].update(namespace_offsets)

    return all_offsets

# Função principal
def generate_files(directory):
    # Processar todos os arquivos .hpp
    all_offsets = process_all_cpp_files(directory)

    # Gera o arquivo JSON
    output_json = 'offsets.json'
    save_offsets_to_json(all_offsets, output_json)

    # Gera o arquivo HPP
    output_hpp = 'offsets.hpp'
    with open(output_hpp, 'w', encoding='utf-8') as hpp_file:
        hpp_file.write(generate_hpp(all_offsets))

    # Gera o arquivo C++ para as atribuições a partir do JSON
    output_cpp = 'set_offsets.cpp'
    generate_cpp_offset_code(output_json, output_cpp)

    print(f"Arquivos gerados: {output_json}, {output_hpp}, {output_cpp}")

# Executa o script
if __name__ == "__main__":
    cpp_directory = 'A2X Generate Files'  # Caminho da pasta com os arquivos .hpp
    generate_files(cpp_directory)
