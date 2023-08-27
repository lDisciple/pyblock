import * as Blockly from 'blockly';
import {pythonGenerator} from 'blockly/python';

export abstract class BlockDefinition {
  abstract getDefinition(): any;
  abstract generate(block, generator): string;
  register() {
    const definition = this.getDefinition();

    Blockly.defineBlocksWithJsonArray([definition]);
    pythonGenerator.forBlock[definition.type] = this.generate;
  }
}
