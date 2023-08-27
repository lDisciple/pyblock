import {BlockDefinition} from '../../../models/block.model';

export default class OnStartBlock extends BlockDefinition{
  generate(block, generator) {
    const code = '...\n';
    return code;
  }

  getDefinition() {
    return {
      type: 'initiator_on_start',
      message0: 'On start',
      nextStatement: null,
      colour: 65,
      tooltip: 'Runs the statements below when the program starts',
      helpUrl: ''
    };
  }
}
